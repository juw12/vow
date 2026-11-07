"""End-to-end test of proof rules (round 5): camera-only photo check-ins, and debts that clear only
with a receipt image or the witness's signed confirmation.

Checks: photo check-in has no file picker and uses a live camera frame; no camera = no photo proof;
a debt won't clear with text alone; a receipt image clears it; a witness-signed payment clears it
(even after the vow is deleted); forged and replayed payment signatures are rejected; someone who
isn't the witness can't sign.
Usage: python check_proof.py <app_dir>
"""
import base64
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
APP = Path(sys.argv[1]).resolve()
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAEklEQVR4nGP4z8CAFWEXHbQSACj/P8Fu7N9hAAAAAElFTkSuQmCC"
)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(APP)))
BASE = f"http://127.0.0.1:{server.server_address[1]}/"
threading.Thread(target=server.serve_forever, daemon=True).start()
results = {}
errors = []


def check(name, ok, note=""):
    results[name] = bool(ok)
    print(("PASS " if ok else "FAIL ") + name + (f" ({note})" if note and not ok else ""), flush=True)


def state(page):
    return page.evaluate("JSON.parse(localStorage.getItem('vow.v1'))")


def make_vow(page, title, proof="witness"):
    page.goto(BASE + "#new")
    page.fill("#f-title", title)
    page.evaluate("document.getElementById('opts') && (document.getElementById('opts').open = true)")
    page.click("#once-box label:has-text('In 1 week')")
    page.click(f"label:has(input[name=proof][value={proof}])")
    page.fill("#f-witness", "Sam")
    page.click("#seal-btn")
    page.wait_for_timeout(1200)
    page.evaluate("document.getElementById('dlg').open && document.getElementById('dlg').close()")
    return state(page)["vows"][-1]["id"]


def accept_as_witness(owner, witness, vow_id):
    witness.goto(owner.evaluate(f"witnessLink(S.vows.find(v => v.id === '{vow_id}'))"))
    witness.click("#w-accept")
    witness.wait_for_selector("#share-link")
    owner.goto(witness.locator("#share-link").input_value())
    owner.wait_for_timeout(700)


def add_debt(page, vow_id):
    debt_id = page.evaluate(
        f"""(() => {{ const v = S.vows.find(x => x.id === '{vow_id}');
        const d = addDebt(v, v.occ[0]); save(); render(); return d.id; }})()"""
    )
    page.goto(BASE)
    page.wait_for_timeout(300)
    return debt_id


def debt(page, debt_id):
    return next(d for d in state(page)["debts"] if d["id"] == debt_id)


def paid_link(page, vow_id, debt_id):
    return page.evaluate(
        f"""(() => {{ const d = S.debts.find(x => x.id === '{debt_id}');
        return appUrl('paid=' + b64e(JSON.stringify({{ id: '{vow_id}', debt: d.id, n: '', t: d.title, s: money(d.amount), to: d.to }}))); }})()"""
    )


with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path=CHROME,
        args=["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"],
    )
    owner_ctx = browser.new_context(viewport={"width": 390, "height": 844}, permissions=["camera"])
    witness_ctx = browser.new_context(viewport={"width": 390, "height": 844})
    stranger_ctx = browser.new_context(viewport={"width": 390, "height": 844})
    nocam_ctx = browser.new_context(viewport={"width": 390, "height": 844})
    nocam_ctx.add_init_script("navigator.mediaDevices.getUserMedia = () => Promise.reject(new Error('denied'));")
    owner, witness, stranger, nocam = (c.new_page() for c in (owner_ctx, witness_ctx, stranger_ctx, nocam_ctx))
    for p in (owner, witness, stranger, nocam):
        p.set_default_timeout(20000)
        p.on("pageerror", lambda e: errors.append(str(e)))
    owner.goto(BASE)

    # 1. camera-only photo check-in
    photo_vow = make_vow(owner, "Clean the kitchen", proof="photo")
    owner.goto(BASE)
    owner.click(f"[data-checkin='{photo_vow}']")
    owner.wait_for_selector("#pvideo")
    check("photo check-in offers no file picker", owner.locator("#pf input[type=file]").count() == 0)
    owner.wait_for_function("!document.querySelector('#psnap').disabled")
    owner.click("#psnap")
    owner.wait_for_selector("#pprev:not([hidden])")
    owner.click("#pf button.primary")
    owner.wait_for_timeout(600)
    occ = next(v for v in state(owner)["vows"] if v["id"] == photo_vow)["occ"][0]
    proof = occ.get("proof") or {}
    check("live camera photo keeps the vow", occ["status"] == "kept" and proof.get("live") is True
          and str(proof.get("photo", "")).startswith("data:image/jpeg"), occ["status"])
    camera_live = owner.evaluate("Array.from(document.querySelectorAll('video')).some(v => v.srcObject && v.srcObject.active)")
    check("camera is released after the check-in", not camera_live)

    # 2. no camera -> no photo proof
    nocam.goto(BASE)
    blocked_vow = make_vow(nocam, "Water the plants", proof="photo")
    nocam.goto(BASE)
    nocam.click(f"[data-checkin='{blocked_vow}']")
    nocam.wait_for_function("document.querySelector('#pcam-hint').textContent.includes(\"can't open a camera\")")
    check("without a camera the photo can't be taken", nocam.locator("#psnap").is_disabled())

    # 3. receipt path: text alone doesn't clear, an image does
    receipt_vow = make_vow(owner, "Go to bed by 11")
    receipt_debt = add_debt(owner, receipt_vow)
    owner.click(f"[data-pay='{receipt_debt}']")
    owner.fill("#pay-ref", "TRX-12345")
    owner.click("#pay-ok")
    owner.wait_for_timeout(400)
    check("a reference alone doesn't clear the debt", debt(owner, receipt_debt)["paidAt"] is None)
    owner.set_input_files("#pay-img", files=[{"name": "receipt.png", "mimeType": "image/png", "buffer": PNG}])
    owner.wait_for_selector("#pay-prev:not([hidden])")
    owner.click("#pay-ok")
    owner.wait_for_timeout(600)
    d = debt(owner, receipt_debt)
    check("a receipt image clears the debt", d["paidAt"] is not None and d.get("paidBy") == "receipt"
          and str(d.get("receiptPhoto", "")).startswith("data:image/jpeg") and d["receipt"] == "TRX-12345")
    owner.evaluate("document.getElementById('dlg').open && document.getElementById('dlg').close()")

    # 4. witness path
    w_vow = make_vow(owner, "No sugar this week")
    accept_as_witness(owner, witness, w_vow)
    w_debt = add_debt(owner, w_vow)
    w_debt2 = add_debt(owner, w_vow)
    check("debt remembers the witness key", debt(owner, w_debt).get("witnessPub") is not None)
    owner.click(f"[data-pay='{w_debt}']")
    check("pay dialog offers the witness option", owner.locator("#pay-ask").count() == 1)
    owner.evaluate("document.getElementById('dlg').close()")

    link = paid_link(owner, w_vow, w_debt)
    stranger.goto(link)
    stranger.wait_for_selector("h1:has-text('Payment check')")
    check("someone else can't sign the payment", stranger.locator("#p-ok").count() == 0)

    forged = owner.evaluate(
        f"b64e(JSON.stringify({{ id: '{w_vow}', debt: '{w_debt}', sig: bytesB64u(new Uint8Array(64).fill(9)) }}))"
    )
    owner.goto(BASE + "#paidok=" + forged)
    owner.wait_for_timeout(800)
    check("forged payment confirmation rejected", debt(owner, w_debt)["paidAt"] is None)

    witness.goto(link)
    witness.click("#p-ok")
    witness.wait_for_function("document.querySelector('#p-link').value.includes('#paidok=')")
    ok_link = witness.locator("#p-link").input_value()

    replay = owner.evaluate(
        f"""(() => {{ const p = JSON.parse(b64d('{ok_link.split('paidok=')[1]}')); p.debt = '{w_debt2}';
        return b64e(JSON.stringify(p)); }})()"""
    )
    owner.goto(BASE + "#paidok=" + replay)
    owner.wait_for_timeout(800)
    check("signature for one debt can't clear another", debt(owner, w_debt2)["paidAt"] is None)

    # the vow is gone by the time the confirmation arrives: the debt still clears
    owner.evaluate(f"S.vows = S.vows.filter(v => v.id !== '{w_vow}'); save();")
    owner.goto(ok_link)
    owner.wait_for_timeout(800)
    d = debt(owner, w_debt)
    check("witness-signed payment clears the debt (vow already deleted)", d["paidAt"] is not None and d.get("paidBy") == "witness")

    check("no page errors", not errors, "; ".join(errors[:3]))
    browser.close()

server.shutdown()
failed = [k for k, v in results.items() if not v]
print(f"{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
