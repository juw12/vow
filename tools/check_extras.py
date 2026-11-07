"""Checks for the v4/v5 additions: 24h walk-away rule, wall-clock focus timer, QR codes on hand-off links,
and debts that clear only with a receipt image or a witness-signed confirmation (two browser profiles).
Live-camera photo proof is covered by check_proof.py.

Usage: python check_extras.py <app_dir>
"""
import functools
import http.server
import json
import os
import socketserver
import struct
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path

import cv2
import numpy as np
from playwright.sync_api import sync_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
APP = Path(sys.argv[1]).resolve()
START = datetime(2026, 11, 9, 10, 0, 0)  # a Monday, 10:00 local
MIN = 60 * 1000


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


socketserver.ThreadingTCPServer.daemon_threads = True
server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(APP)))
BASE = f"http://127.0.0.1:{server.server_address[1]}/"
threading.Thread(target=server.serve_forever, daemon=True).start()
results = {}
errors = []


def check(name, ok, note=""):
    results[name] = bool(ok)
    print(("PASS " if ok else "FAIL ") + name + (f"  ({note})" if note else ""), flush=True)


def state(page):
    return page.evaluate("JSON.parse(localStorage.getItem('vow.v1') || 'null')")


def new_page(browser, clock=False, scale=1):
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=scale)
    page = ctx.new_page()
    page.set_default_timeout(20000)
    page.on("pageerror", lambda e: errors.append(str(e)))
    if clock:
        page.clock.install(time=START)
    page.goto(BASE)
    page.wait_for_selector("#view")
    return ctx, page


def settle(page, clock, ms=1200):
    if clock:
        page.clock.run_for(ms)
    else:
        page.wait_for_timeout(ms)


def close_dialog(page):
    page.evaluate("document.getElementById('dlg').open && document.getElementById('dlg').close()")


def make_vow(page, title, proof="note", when=None, timer_min=None, clock=False):
    page.goto(BASE + "#new")
    page.wait_for_selector("#f-title")
    page.fill("#f-title", title)
    page.evaluate("document.getElementById('opts') && (document.getElementById('opts').open = true)")
    if when:
        page.click(f"#once-box label:has-text('{when}')")
    page.click(f"label:has(input[name=proof][value={proof}])")
    if timer_min:
        page.fill("#f-timer", str(timer_min))
    page.fill("#f-witness", "Sam")
    page.click("#seal-btn")
    settle(page, clock)
    close_dialog(page)
    return state(page)["vows"][-1]["id"]


def more(page, vow_id, action):
    card = page.locator(f"[data-vow='{vow_id}']")
    card.locator("summary").click()
    card.locator(f"button[data-act='{action}']").click()


def set_visibility(page, value):
    page.evaluate(
        """(v) => {
          Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => v });
          Object.defineProperty(document, 'hidden', { configurable: true, get: () => v !== 'visible' });
          document.dispatchEvent(new Event('visibilitychange'));
        }""",
        value,
    )


def jpeg_with_exif(taken: datetime) -> bytes:
    """A real 64x64 JPEG with an APP1 Exif block holding DateTimeOriginal (little-endian TIFF)."""
    img = np.full((64, 64, 3), 200, np.uint8)
    cv2.rectangle(img, (10, 10), (54, 54), (40, 40, 160), -1)
    ok, buf = cv2.imencode(".jpg", img)
    jpg = buf.tobytes()
    stamp = taken.strftime("%Y:%m:%d %H:%M:%S").encode() + b"\x00"  # 20 bytes
    # TIFF: header(8) + IFD0 (2 + 12 + 4) + ExifIFD (2 + 12 + 4) + value
    ifd0_off = 8
    exif_off = ifd0_off + 2 + 12 + 4
    value_off = exif_off + 2 + 12 + 4
    tiff = b"II*\x00" + struct.pack("<I", ifd0_off)
    tiff += struct.pack("<H", 1) + struct.pack("<HHII", 0x8769, 4, 1, exif_off) + struct.pack("<I", 0)
    tiff += struct.pack("<H", 1) + struct.pack("<HHII", 0x9003, 2, len(stamp), value_off) + struct.pack("<I", 0)
    tiff += stamp
    body = b"Exif\x00\x00" + tiff
    app1 = b"\xff\xe1" + struct.pack(">H", len(body) + 2) + body
    return jpg[:2] + app1 + jpg[2:]


def render_modules(modules, scale=8, quiet=4):
    size = len(modules)
    img = np.full(((size + 2 * quiet) * scale,) * 2, 255, np.uint8)
    for y, row in enumerate(modules):
        for x, cell in enumerate(row):
            if cell:
                y0 = (y + quiet) * scale
                x0 = (x + quiet) * scale
                img[y0:y0 + scale, x0:x0 + scale] = 0
    return img


def decode_qr(img):
    """Decode with OpenCV's classic detector, falling back to the Aruco-based one."""
    text, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
    if not text:
        text, _, _ = cv2.QRCodeDetectorAruco().detectAndDecode(img)
    return text


def decode_png(png_bytes):
    arr = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
    arr = cv2.copyMakeBorder(arr, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=255)
    return decode_qr(arr)


with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME)

    # 1. 24h walk-away rule ---------------------------------------------------
    ctx, page = new_page(browser, clock=True)
    far = make_vow(page, "Finish the tax return", when="In 1 week", clock=True)
    near = make_vow(page, "Call grandma", when="Tomorrow 9:00", clock=True)
    page.clock.fast_forward(11 * MIN)
    page.goto(BASE)
    more(page, far, "delete")
    check("delete of a vow due in a week opens walk-away", page.locator("#dlg[open] #wf").count() == 1)
    close_dialog(page)
    page.clock.fast_forward(3 * 60 * MIN)  # 13:11, tomorrow 9:00 is under 24h away
    page.goto(BASE)
    more(page, near, "delete")
    check("delete of a vow due within 24h asks for a free scheduled delete",
          page.locator("#dlg[open] #askv").count() == 1 and page.locator("#dlg[open] #wf").count() == 0)
    close_dialog(page)
    ctx.close()

    # 2. wall-clock focus timer --------------------------------------------
    ctx, page = new_page(browser, clock=True)
    focus = make_vow(page, "Deep work block", proof="timer", timer_min=1, clock=True)
    page.clock.fast_forward(11 * MIN)
    page.goto(BASE)
    page.click(f"[data-checkin='{focus}']")
    page.click("#tstart")
    page.clock.run_for(5000)
    set_visibility(page, "hidden")
    page.clock.run_for(20000)
    set_visibility(page, "visible")
    page.clock.run_for(1000)
    restarted = page.locator("#tstart").is_enabled() and "again" in page.locator("#tstart").inner_text().lower()
    check("leaving for 20s restarts the focus session", restarted)
    page.click("#tstart")
    page.clock.run_for(10000)
    set_visibility(page, "hidden")
    page.clock.run_for(8000)  # short glance away: under the 15s limit
    set_visibility(page, "visible")
    page.clock.run_for(45000)
    occ = next(v for v in state(page)["vows"] if v["id"] == focus)["occ"][0]
    check("timer counts wall-clock time and keeps after 60s with a short glance away",
          occ["status"] == "kept" and occ["proof"]["type"] == "timer" and occ["proof"].get("startedAt"))
    ctx.close()

    # 4. QR on the witness invite ---------------------------------------------
    ctx, page = new_page(browser, scale=2)
    qv = make_vow(page, "Run 5 km")
    page.goto(BASE)
    page.locator(f"[data-vow='{qv}'] button.pill[data-act='witness']").click()
    page.wait_for_selector("#dlg[open] svg.qr")
    link = page.evaluate(f"witnessLink(S.vows.find(v => v.id === '{qv}'))")
    svg = page.locator("#dlg[open] svg.qr").first
    modules = page.evaluate("(t) => QR.encode(t).modules.map((r) => r.map((c) => (c ? 1 : 0)))", link)
    check("invite QR matrix decodes to the invite link (OpenCV)", decode_qr(render_modules(modules)) == link)
    check("on-screen invite QR decodes from a 2x screenshot", decode_png(svg.screenshot()) == link)
    rendered = svg.get_attribute("viewBox").split()[2]
    check("rendered QR carries a 4-module quiet zone", int(rendered) == len(modules) + 8)
    check("QR has an accessible name", bool(svg.get_attribute("aria-label")))
    box = svg.bounding_box()
    check("QR fits a 390px screen", box and box["x"] >= 0 and box["x"] + box["width"] <= 390)
    ctx.close()

    # 5. debts clear only with a receipt image or a witness-signed confirmation (two profiles)
    owner_ctx, owner = new_page(browser)
    witness_ctx, witness = new_page(browser)
    vid = make_vow(owner, "No sugar this week", when="In 1 week")
    other = make_vow(owner, "Read 20 pages", when="In 1 week")
    third = make_vow(owner, "Walk 8,000 steps", when="In 1 week")
    for target in (vid, other, third):
        invite = owner.evaluate(f"witnessLink(S.vows.find(v => v.id === '{target}'))")
        witness.goto(invite)
        witness.click("#w-accept")
        witness.wait_for_selector("#share-link")
        owner.goto(witness.locator("#share-link").input_value())
        owner.wait_for_timeout(700)
    owner.evaluate(
        f"""() => {{
          for (const id of ['{vid}', '{other}', '{third}']) {{
            const v = S.vows.find((x) => x.id === id);
            addDebt(v, v.occ[0]);
          }}
          save();
          render();
        }}"""
    )
    debts = state(owner)["debts"]
    debt_a = next(d for d in debts if d["vowId"] == vid)["id"]
    debt_b = next(d for d in debts if d["vowId"] == other)["id"]
    debt_c = next(d for d in debts if d["vowId"] == third)["id"]
    owner.goto(BASE)

    owner.click(f"[data-pay='{debt_b}']")
    owner.click("#pay-ok")
    owner.wait_for_timeout(300)
    check("'I paid' without a receipt image does not clear the debt",
          next(d for d in state(owner)["debts"] if d["id"] == debt_b)["paidAt"] is None)
    owner.set_input_files("#pay-img", files=[{"name": "r.jpg", "mimeType": "image/jpeg", "buffer": jpeg_with_exif(datetime.now())}])
    owner.wait_for_function("!document.getElementById('pay-prev').hidden")
    owner.fill("#pay-ref", "TXN-88213")
    owner.click("#pay-ok")
    owner.wait_for_timeout(500)
    paid_b = next(d for d in state(owner)["debts"] if d["id"] == debt_b)
    check("receipt image clears the debt and is stored",
          paid_b["paidAt"] and paid_b.get("receiptPhoto", "").startswith("data:image/jpeg") and paid_b["receipt"] == "TXN-88213")
    close_dialog(owner)

    owner.goto(BASE)
    owner.click(f"[data-pay='{debt_a}']")
    owner.click("#pay-ask")
    owner.wait_for_selector("#pay-ask-out svg.qr")
    req_link = owner.locator("#pay-ask-out textarea").input_value()
    check("ask-witness shows the request link with a QR", "#paid=" in req_link)
    check("asking does not clear the debt", next(d for d in state(owner)["debts"] if d["id"] == debt_a)["paidAt"] is None)
    close_dialog(owner)
    owner.goto(BASE)
    check("owed banner notes the pending request", "asked Sam to confirm" in owner.inner_text("#view"))

    witness.goto(req_link)
    witness.wait_for_selector("#p-ok")
    witness.click("#p-ok")
    witness.wait_for_function("document.querySelector('#p-link') && document.querySelector('#p-link').value.includes('#paidok=')")
    ok_link = witness.locator("#p-link").input_value()
    check("witness confirmation has a QR", witness.locator("#p-qr svg.qr").count() == 1)

    forged = owner.evaluate(f"b64e(JSON.stringify({{id: '{vid}', debt: '{debt_a}', sig: bytesB64u(new Uint8Array(64).fill(9))}}))")
    owner.goto(BASE + "#paidok=" + forged)
    owner.wait_for_timeout(800)
    check("forged payment confirmation is rejected",
          next(d for d in state(owner)["debts"] if d["id"] == debt_a)["paidAt"] is None)

    payload = json.loads(owner.evaluate(f"b64d('{ok_link.split('paidok=')[1]}')"))
    replay = dict(payload, id=third, debt=debt_c)
    owner.goto(BASE + "#paidok=" + owner.evaluate(f"b64e(JSON.stringify({json.dumps(replay)}))"))
    owner.wait_for_timeout(800)
    check("confirmation can't be replayed on another debt",
          next(d for d in state(owner)["debts"] if d["id"] == debt_c)["paidAt"] is None)

    owner.goto(ok_link)
    owner.wait_for_timeout(800)
    confirmed = next(d for d in state(owner)["debts"] if d["id"] == debt_a)
    check("real witness signature clears the debt", confirmed["paidAt"] and confirmed.get("paidBy") == "witness")
    owner.goto(BASE + "#history")
    owner.wait_for_timeout(300)
    check("history shows the confirmation", "confirmed by Sam" in owner.inner_text("#view"))

    check("no page errors", not errors, "; ".join(errors[:2]))
    print(json.dumps({"all_pass": all(results.values()), "passed": sum(results.values()), "total": len(results)}), flush=True)
    os._exit(0 if all(results.values()) else 1)
