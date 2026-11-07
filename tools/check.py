"""Hard-gate checker for Vow (rubric v1, gates G1-G10) + judge screenshots.

Usage: python check.py <app_dir> <shots_dir>
Prints one line per gate and a JSON summary; exit code 0 only if every gate passes.
"""
import functools
import os
import http.server
import json
import socketserver
import sys
import threading
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
APP = Path(sys.argv[1]).resolve()
SHOTS = Path(sys.argv[2]).resolve()
SHOTS.mkdir(parents=True, exist_ok=True)
START = datetime(2026, 11, 9, 10, 0, 0)  # a Monday, 10:00 local
HOUR = 3600 * 1000
MIN = 60 * 1000

results = {}
errors = []
foreign = []


def gate(name, ok, note=""):
    results[name] = {"ok": bool(ok), "note": note}
    print(f"{'PASS' if ok else 'FAIL'} {name} {note}", flush=True)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


handler = functools.partial(QuietHandler, directory=str(APP))
server = socketserver.TCPServer(("127.0.0.1", 0), handler)
port = server.server_address[1]
BASE = f"http://127.0.0.1:{port}/"
threading.Thread(target=server.serve_forever, daemon=True).start()


def watch(page):
    page.on("console", lambda m: errors.append(f"console: {m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.on("request", lambda r: foreign.append(r.url) if r.url.startswith("http") and not r.url.startswith(BASE) else None)


def shot(page, path, full_page=False):
    page.evaluate("window.scrollTo(0, 0)")
    for attempt in range(3):
        try:
            page.screenshot(path=path, full_page=full_page, timeout=15000)
            return
        except Exception as err:
            print(f"  screenshot retry {attempt + 1}: {str(err).splitlines()[0]}", flush=True)
            try:
                page.clock.run_for(1000)
            except Exception:
                pass
    raise RuntimeError(f"screenshot failed: {path}")


def state(page):
    return page.evaluate("JSON.parse(localStorage.getItem('vow.v1') || 'null')")


def fresh(browser, width=390, height=844, scheme="light", clock=True):
    ctx = browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme, accept_downloads=True)
    page = ctx.new_page()
    page.set_default_timeout(25000)
    watch(page)
    if clock:
        page.clock.install(time=START)
    page.goto(BASE)
    page.wait_for_selector("#view")
    return ctx, page


def close_dialog(page):
    page.evaluate("document.getElementById('dlg').open && document.getElementById('dlg').close()")


def make_vow(page, title, proof="note", when=None, stake=None, witness="Sam"):
    print(f"  make_vow {title!r}", flush=True)
    page.goto(BASE + "#new")
    page.wait_for_selector("#f-title")
    page.fill("#f-title", title)
    page.evaluate("document.getElementById('opts') && (document.getElementById('opts').open = true)")
    if when:
        page.click(f"#once-box label:has-text('{when}')")
    if stake:
        page.click(f"label:has-text('{stake}') >> nth=0")
    page.click(f"label:has(input[name=proof][value={proof}])")
    page.fill("#f-witness", witness)
    page.click("#seal-btn")
    page.clock.run_for(1500)
    close_dialog(page)
    return state(page)["vows"][-1]["id"]


def more(page, vow_id, action):
    card = page.locator(f"[data-vow='{vow_id}']")
    card.locator("summary").click()
    card.locator(f"button[data-act='{action}']").click()


def answer(page, value):
    page.fill("#askv", str(value))
    page.click("#askf button.primary")


with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME)

    # G2 keep with proof -------------------------------------------------
    ctx, page = fresh(browser)
    shot(page, path=str(SHOTS / "01-empty-mobile.png"))
    vid = make_vow(page, "Run 5 km along the coast")
    page.clock.fast_forward(11 * MIN)
    page.click(f"[data-checkin='{vid}']")
    page.fill("#pnote", "Ran 5.2 km in 31 minutes, felt great")
    page.click("#pf button.primary")
    page.clock.run_for(1500)
    s = state(page)
    occ = s["vows"][0]["occ"][0]
    gate("G2 keep-with-proof", occ["status"] == "kept" and occ["proof"]["type"] == "note", occ["status"])
    ctx.close()

    # G3 auto-break at the deadline -------------------------------------
    ctx, page = fresh(browser)
    vid = make_vow(page, "Write 500 words")
    page.clock.fast_forward(15 * HOUR)
    page.clock.run_for(6000)
    s = state(page)
    debts = s["debts"]
    dialog_text = page.locator("#dlg").inner_text() if page.locator("#dlg[open]").count() else ""
    ok = (s["vows"][0]["occ"][0]["status"] == "broken" and len(debts) == 1 and debts[0]["amount"] == 10
          and "I broke my vow" in page.locator("#dlg textarea").input_value())
    shot(page, path=str(SHOTS / "05-broken-confess.png"))
    close_dialog(page)
    shot(page, path=str(SHOTS / "06-owed-home.png"), full_page=True)
    gate("G3 auto-break+debt+confession", ok, f"debts={len(debts)}")
    ctx.close()

    # G4 easing is delayed, raising is instant --------------------------
    ctx, page = fresh(browser)
    vid = make_vow(page, "Study for 1 hour", when="In 1 week")
    page.clock.fast_forward(11 * MIN)
    more(page, vid, "raise")
    answer(page, 20)
    raised = state(page)["vows"][0]["stake"] == 20
    more(page, vid, "lower")
    answer(page, 5)
    s = state(page)
    lowered_waits = s["vows"][0]["stake"] == 20 and len(s["vows"][0]["pending"]) == 1
    more(page, vid, "delete")
    # a far-off vow can't be deleted for free: the walk-away dialog opens, not the type-DELETE ask
    walk_open = page.locator("#w-debt").count() == 1 and page.locator("#askv").count() == 0
    shot(page, path=str(SHOTS / "04-pending-change.png"), full_page=True)
    close_dialog(page)
    page.clock.fast_forward(24 * HOUR + 10 * MIN)
    s = state(page)
    applied = s["vows"][0]["stake"] == 5 and s["vows"][0]["status"] == "active"
    gate("G4 easing-delayed-24h", raised and lowered_waits and walk_open and applied,
         f"raised={raised} waits={lowered_waits} walk={walk_open} applied={applied}")
    ctx.close()

    # G11 deleting a far-off vow costs: owe the stake, or the witness signs off --
    ctx, page = fresh(browser)
    far = make_vow(page, "Save money for a trip", when="In 1 week")
    page.clock.fast_forward(11 * MIN)
    more(page, far, "delete")
    walk = page.locator("#w-debt").count() == 1 and page.locator("#askv").count() == 0
    page.click("#w-debt")
    page.clock.run_for(1500)
    s = state(page)
    fv = s["vows"][0]
    debt_ok = any(d.get("bailout") and d["amount"] == 10 and not d["paidAt"] for d in s["debts"])
    far_active = fv["status"] == "active" and len(fv["pending"]) == 1 and fv["pending"][0]["type"] == "delete"
    close_dialog(page)
    shot(page, path=str(SHOTS / "09-walkaway-debt.png"), full_page=True)
    near = make_vow(page, "Pay the rent")
    page.clock.fast_forward(11 * MIN)
    more(page, near, "delete")
    free = page.locator("#askv").count() == 1 and page.locator("#w-debt").count() == 0
    answer(page, "DELETE")
    near_active = state(page)["vows"][-1]["status"] == "active"
    gate("G11 far-off-delete-costs", walk and debt_ok and far_active and free and near_active,
         f"walk={walk} debt={debt_ok} faractive={far_active} free={free} near={near_active}")
    ctx.close()

    # G5 grace pass: before deadline only, 1 per 30 days ----------------
    ctx, page = fresh(browser)
    v1 = make_vow(page, "Go to the gym", when="In 1 week")
    v2 = make_vow(page, "Send the report", when="In 1 week")
    page.clock.fast_forward(11 * MIN)
    more(page, v1, "pass")
    answer(page, "Flu, doctor said rest")
    page.wait_for_timeout(200)
    close_dialog(page)
    first = state(page)["vows"][0]["occ"][0]["status"] == "excused"
    more(page, v2, "pass")
    page.clock.run_for(500)
    second_blocked = page.locator("#dlg[open] #askv").count() == 0 and state(page)["vows"][1]["occ"][0]["status"] == "open"
    close_dialog(page)
    gate("G5 grace-pass-rules", first and second_blocked, f"first={first} second_blocked={second_blocked}")
    ctx.close()

    # G6 persistence + export/import ------------------------------------
    ctx, page = fresh(browser)
    make_vow(page, "Run 5 km")
    make_vow(page, "No phone after 23:00", proof="photo")
    before = state(page)
    page.reload()
    page.wait_for_selector("#view")
    after_reload = state(page)
    page.goto(BASE + "#settings")
    with page.expect_download() as dl:
        page.click("#export")
    backup = Path(dl.value.path()).read_text(encoding="utf-8")
    page.click("#erase")
    answer(page, "ERASE")
    erased = len(state(page)["vows"]) == 0
    page.goto(BASE + "#settings")
    page.set_input_files("#import-file", files=[{"name": "b.json", "mimeType": "application/json", "buffer": backup.encode()}])
    page.wait_for_timeout(300)
    restored = state(page)
    ok = before == after_reload and erased and restored["vows"] == before["vows"]
    gate("G6 persist+export/import", ok, f"erased={erased}")
    ctx.close()

    # G10 calendar export -----------------------------------------------
    ctx, page = fresh(browser)
    vid = make_vow(page, "Run 5 km")
    page.locator(f"[data-vow='{vid}'] summary").click()
    with page.expect_download() as dl:
        page.locator(f"[data-vow='{vid}'] button[data-act='ics']").click()
    ics = Path(dl.value.path()).read_bytes().decode("utf-8")
    ok = all(k in ics for k in ["BEGIN:VCALENDAR", "BEGIN:VEVENT", "DTSTART:", "BEGIN:VALARM", "TRIGGER:-PT", "END:VCALENDAR"]) and "\r\n" in ics
    gate("G10 ics-with-alarm", ok)
    ctx.close()

    # G7 + G9 + screenshots: layouts at all widths, both themes ----------
    overflow = []
    unnamed = set()
    name_js = """() => {
      const els = [...document.querySelectorAll('button, a[href], input, select, textarea, summary')];
      const bad = [];
      for (const el of els) {
        if (el.type === 'hidden') continue;
        let n = el.getAttribute('aria-label') || '';
        const lb = el.getAttribute('aria-labelledby');
        if (!n && lb) n = lb.split(' ').map(id => (document.getElementById(id) || {}).textContent || '').join(' ');
        if (!n && el.labels && el.labels.length) n = [...el.labels].map(l => l.textContent).join(' ');
        if (!n && !['INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName)) n = el.textContent;
        if (!n) n = el.getAttribute('title') || el.getAttribute('placeholder') || '';
        if (!n.trim()) bad.push(el.outerHTML.slice(0, 80));
      }
      return bad;
    }"""
    for scheme in ("light", "dark"):
        for width in (320, 390, 768, 1024, 1440):
            ctx, page = fresh(browser, width=width, height=900, scheme=scheme)
            make_vow(page, "Go to the gym for 45 minutes", witness="Sam")
            vid = make_vow(page, "Write 500 words", when="In 1 week")
            for route in ("", "#new", "#history", "#settings"):
                page.goto(BASE + route)
                page.wait_for_timeout(100)
                sw, cw = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
                if sw > cw:
                    overflow.append(f"{scheme}/{width}/{route or 'home'} {sw}>{cw}")
                unnamed.update(page.evaluate(name_js))
                if width == 390 and scheme == "light" and route == "#new":
                    shot(page, path=str(SHOTS / "02-new-vow-mobile.png"), full_page=True)
            page.goto(BASE)
            page.wait_for_timeout(100)
            page.locator(f"[data-vow='{vid}'] summary").click()
            unnamed.update(page.evaluate(name_js))
            page.locator(f"[data-vow='{vid}'] summary").click()
            if width == 390:
                shot(page, path=str(SHOTS / f"03-home-mobile-{scheme}.png"), full_page=True)
            if width == 1440 and scheme == "light":
                shot(page, path=str(SHOTS / "07-home-desktop.png"))
            if width == 390 and scheme == "light":
                s = state(page)
                v = s["vows"][0]
                link = page.evaluate(f"witnessLink(S.vows[0])")
                page.goto(link)
                page.wait_for_timeout(300)
                unnamed.update(page.evaluate(name_js))
                shot(page, path=str(SHOTS / "08-witness-page.png"), full_page=True)
            ctx.close()
    gate("G7 no-overflow", not overflow, "; ".join(overflow[:6]))
    gate("G9 accessible-names", not unnamed, "; ".join(sorted(unnamed)[:4]))

    # G8 offline + installable + no foreign requests ---------------------
    ctx, page = fresh(browser, clock=False)
    sw_ok = page.evaluate("navigator.serviceWorker.ready.then(r => !!r.active)")
    manifest = page.evaluate("fetch('manifest.webmanifest').then(r => r.json())")
    sizes = {i.get("sizes") for i in manifest.get("icons", [])}
    man_ok = bool(manifest.get("name")) and manifest.get("display") == "standalone" and {"192x192", "512x512"} <= sizes
    ctx.set_offline(True)
    page.reload()
    offline_ok = page.locator("#view").count() == 1 and "Vow" in page.title()
    ctx.close()
    gate("G8 offline+installable+local-only", sw_ok and man_ok and offline_ok and not foreign,
         f"sw={sw_ok} manifest={man_ok} offline={offline_ok} foreign={foreign[:3]}")

    gate("G1 no-console-errors", not errors, "; ".join(errors[:5]))
    order = sorted(results)
    summary = {"all_pass": all(results[k]["ok"] for k in order), "gates": results}
    (SHOTS / "gates.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"all_pass": summary["all_pass"], "failed": [k for k in order if not results[k]["ok"]]}), flush=True)
    # browser.close() can hang on Windows with a live service worker; the results are already written
    os._exit(0 if summary["all_pass"] else 1)
