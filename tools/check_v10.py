"""End-to-end tests for the v10 features, with two browser profiles (owner and witness).

V2 note instead of photo, V3 solo vows, V4 witness response window, V5 witness-tracked debts,
V6 witness-approved passes, V7 changing proof type after sealing.
Usage: python check_v10.py <app_dir>
"""
import functools
import http.server
import json
import re
import socketserver
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
APP = Path(sys.argv[1]).resolve()


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def safe_server():
    # Chrome refuses some ports (e.g. 2049), so stay in a plain high range.
    import random
    for port in random.sample(range(18100, 18900), 40):
        try:
            return socketserver.TCPServer(("127.0.0.1", port), functools.partial(QuietHandler, directory=str(APP)))
        except OSError:
            continue
    raise SystemExit("no free port")


server = safe_server()
BASE = f"http://127.0.0.1:{server.server_address[1]}/"
threading.Thread(target=server.serve_forever, daemon=True).start()
results = {}
errors = []


def check(name, ok, note=""):
    results[name] = bool(ok)
    print(("PASS " if ok else "FAIL ") + name + (f"  ({note})" if note and not ok else ""), flush=True)


def state(page):
    return page.evaluate("JSON.parse(localStorage.getItem('vow.v1'))")


def vow(page, vid):
    return next(x for x in state(page)["vows"] if x["id"] == vid)


def close_dialog(page):
    page.evaluate("document.getElementById('dlg').open && document.getElementById('dlg').close()")


def nav(page, url):
    """Full load for every link: hash-only jumps on the same page never fire 'load'."""
    page.goto("about:blank")
    page.goto(url)


def make_vow(page, title, proof="note", witness="Sam"):
    nav(page, BASE + "#new")
    page.fill("#f-title", title)
    page.evaluate("document.getElementById('opts') && (document.getElementById('opts').open = true)")
    page.click("#once-box label:has-text('In 1 week')")
    page.click(f"label:has(input[name=proof][value={proof}])")
    page.fill("#f-witness", witness)
    before = len(state(page)["vows"]) if page.evaluate("!!localStorage.getItem('vow.v1')") else 0
    page.click("#seal-btn")
    page.wait_for_timeout(1100)
    after = state(page)["vows"]
    close_dialog(page)
    return after[-1]["id"] if len(after) > before else None


def pair(owner, witness, vid):
    invite = owner.evaluate(f"witnessLink(S.vows.find(v => v.id === '{vid}'))")
    nav(witness, invite)
    witness.click("#w-accept")
    witness.wait_for_selector("#share-link")
    nav(owner, witness.locator("#share-link").input_value())
    owner.wait_for_timeout(700)


def shift_due(page, vid, hours_ago):
    page.evaluate(f"""(() => {{
        const v = S.vows.find(x => x.id === '{vid}');
        openOcc(v).due = Date.now() - {hours_ago} * 3600e3;
        save();
        tick();
    }})()""")
    page.wait_for_timeout(400)


with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME)
    owner = browser.new_context(viewport={"width": 390, "height": 844}).new_page()
    witness = browser.new_context(viewport={"width": 390, "height": 844}).new_page()
    for p in (owner, witness):
        p.set_default_timeout(20000)
        p.on("pageerror", lambda e: errors.append(str(e)))
    nav(owner, BASE)

    # V3 solo vow: no witness needed, check-in counts on your word
    solo = make_vow(owner, "Stretch for 10 minutes", proof="note", witness="")
    check("solo vow can be sealed without a witness", solo is not None)
    sv = vow(owner, solo)
    check("solo vow stores no witness", sv["witness"] == "" and sv.get("witnessPub") is None)
    nav(owner, BASE)
    check("solo vow card says Solo", "Solo" in owner.inner_text(f"[data-vow='{solo}']"))
    owner.click(f"[data-checkin='{solo}']")
    owner.fill("#pnote", "Did the full stretching routine twice")
    owner.click("#pf button.primary")
    owner.wait_for_timeout(500)
    check("solo check-in keeps the vow at once", vow(owner, solo)["occ"][0]["status"] == "kept")

    blocked = make_vow(owner, "Meditate", proof="witness", witness="")
    check("witness-code proof without a witness is refused", blocked is None)

    # V3 add a witness later
    later = make_vow(owner, "Read 20 pages", proof="note", witness="")
    nav(owner, BASE)
    owner.evaluate(f"() => {{ void act('witness', S.vows.find(v => v.id === '{later}')); }}")
    owner.wait_for_selector("#askf")
    owner.fill("#askf input", "Robin")
    owner.click("#askf button.primary")
    owner.wait_for_timeout(600)
    check("adding a witness later opens the invite", owner.locator("#dlg[open] #wsend").count() == 1
          and vow(owner, later)["witness"] == "Robin")
    close_dialog(owner)

    # V2 note instead of photo
    photo = make_vow(owner, "Clean the desk", proof="photo", witness="")
    nav(owner, BASE)
    owner.click(f"[data-checkin='{photo}']")
    owner.click("#pnote-alt")
    owner.fill("#pnote", "Cleared and wiped the whole desk surface")
    owner.click("#pf button.primary")
    owner.wait_for_timeout(500)
    occ = vow(owner, photo)["occ"][0]
    check("photo vow accepts a note instead", occ["status"] == "kept" and occ["proof"]["type"] == "note"
          and occ["proof"].get("instead") == "photo")
    nav(owner, BASE + "#history")
    check("history marks the note instead of photo", "note instead of photo" in owner.inner_text("#view"))

    # V4 witness response window
    trust = make_vow(owner, "Run 5 km", proof="note")
    pair(owner, witness, trust)
    check("response window is on by default", vow(owner, trust).get("autoAccept") is True)
    nav(owner, BASE)
    owner.click(f"[data-checkin='{trust}']")
    owner.fill("#pnote", "Ran 5.3 km along the river, 29 minutes")
    owner.click("#pf button.primary")
    owner.wait_for_timeout(500)
    close_dialog(owner)
    check("paired check-in is still a claim", vow(owner, trust)["occ"][0]["status"] == "open")
    shift_due(owner, trust, 23)
    check("claim still waits within 24 h of the deadline", vow(owner, trust)["occ"][0]["status"] == "open")
    shift_due(owner, trust, 25)
    close_dialog(owner)
    o = vow(owner, trust)["occ"][0]
    check("silent witness: claim counts after 24 h", o["status"] == "kept" and o["proof"].get("unconfirmed") is True)

    strict = make_vow(owner, "Write 500 words", proof="note")
    pair(owner, witness, strict)
    owner.evaluate(f"S.vows.find(v => v.id === '{strict}').autoAccept = false; save()")
    nav(owner, BASE)
    owner.click(f"[data-checkin='{strict}']")
    owner.fill("#pnote", "Wrote 520 words of chapter two draft")
    owner.click("#pf button.primary")
    owner.wait_for_timeout(500)
    close_dialog(owner)
    shift_due(owner, strict, 25)
    close_dialog(owner)
    check("strict vow: silent witness means broken", vow(owner, strict)["occ"][0]["status"] == "broken")

    # V7 change proof type (waits 24 h)
    nav(owner, BASE)
    owner.evaluate(f"() => {{ void act('proof', S.vows.find(v => v.id === '{later}')); }}")
    owner.wait_for_selector("#prf")
    owner.click("#prf label:has(input[value=timer])")
    owner.click("#prf button.primary")
    owner.wait_for_timeout(400)
    lv = vow(owner, later)
    pend = [p for p in lv.get("pending", []) if p["type"] == "proof"]
    check("proof change is scheduled, not instant", lv["proof"] == "note" and len(pend) == 1)
    owner.evaluate(f"(() => {{ const v = S.vows.find(x => x.id === '{later}'); v.pending.forEach(p => p.at = Date.now() - 1000); save(); tick(); }})()")
    owner.wait_for_timeout(300)
    check("proof change applies after 24 h", vow(owner, later)["proof"] == "timer")

    # V6 pass needs the witness
    pv = make_vow(owner, "Gym 3 times this week", proof="note")
    pair(owner, witness, pv)
    nav(owner, BASE)
    owner.evaluate(f"() => {{ void act('pass', S.vows.find(v => v.id === '{pv}')); }}")
    owner.wait_for_selector("#askf")
    owner.fill("#askf input", "Sprained my ankle on Monday")
    owner.click("#askf button.primary")
    owner.wait_for_timeout(600)
    po = vow(owner, pv)["occ"][0]
    check("pass with a witness is only a request", po["status"] == "open" and po.get("passAsked") is not None)
    check("pass request shows a link to send", owner.locator("#dlg[open] #psend").count() == 1)
    close_dialog(owner)

    forged = owner.evaluate(f"b64e(JSON.stringify({{id: '{pv}', occ: '{po['id']}', sig: bytesB64u(new Uint8Array(64).fill(3))}}))")
    nav(owner, BASE + "#passok=" + forged)
    owner.wait_for_timeout(700)
    check("forged pass approval rejected", vow(owner, pv)["occ"][0]["status"] == "open")

    req = owner.evaluate(f"(() => {{ const v = S.vows.find(x => x.id === '{pv}'); return passLink(v, openOcc(v)); }})()")
    nav(witness, req)
    check("witness sees the reason", "Sprained my ankle" in witness.inner_text("#view"))
    witness.click("#x-allow")
    witness.wait_for_function("document.querySelector('#x-link') && document.querySelector('#x-link').value.includes('#passok=')")
    nav(owner, witness.locator("#x-link").input_value())
    owner.wait_for_timeout(800)
    po = vow(owner, pv)["occ"][0]
    check("witness-approved pass excuses the check-in", po["status"] == "excused" and po.get("excusedBy") == "witness")

    # V5 a missed vow reaches the witness, who tracks it and confirms payment
    mv = make_vow(owner, "No sugar today", proof="note")
    pair(owner, witness, mv)
    nav(owner, BASE)
    shift_due(owner, mv, 1)
    msg = owner.evaluate("(() => { const t = document.querySelector('#dlg[open] textarea'); return t ? t.value : ''; })()")
    m = re.search(r"https?://\S+#owe=\S+", msg)
    check("confession carries a link for the witness", m is not None, msg[:120])
    close_dialog(owner)
    debt_id = next(d for d in state(owner)["debts"] if d["vowId"] == mv)["id"]
    if m:
        nav(witness, m.group(0))
        witness.click("#o-track")
        witness.wait_for_timeout(400)
        wl = witness.evaluate("JSON.parse(localStorage.getItem('vow.witnessing'))")
        tracked = next(w for w in wl if w["id"] == mv).get("debts", [])
        check("witness tracks the debt", any(d["id"] == debt_id and not d["paid"] for d in tracked))
        nav(witness, BASE)
        check("witness home lists the unpaid debt", witness.locator(f"[data-wpaid='{mv}:{debt_id}']").count() == 1)
        witness.click(f"[data-wpaid='{mv}:{debt_id}']")
        witness.click("#wpf button.primary")
        witness.wait_for_function("document.querySelector('#wpf-link') && document.querySelector('#wpf-link').value.includes('#paidok=')")
        nav(owner, witness.locator("#wpf-link").input_value())
        owner.wait_for_timeout(800)
        d = next(x for x in state(owner)["debts"] if x["id"] == debt_id)
        check("witness confirmation clears the debt", d["paidAt"] is not None and d.get("paidBy") == "witness")
        wl = witness.evaluate("JSON.parse(localStorage.getItem('vow.witnessing'))")
        check("witness list marks it paid", any(x["id"] == debt_id and x["paid"] for x in next(w for w in wl if w["id"] == mv)["debts"]))

    check("no page errors", not errors, "; ".join(errors[:3]))
    browser.close()

failed = [k for k, v in results.items() if not v]
print(json.dumps({"passed": len(results) - len(failed), "failed": failed}))
sys.exit(1 if failed else 0)
