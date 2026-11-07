"""End-to-end test of the signed-witness flow (round 2): two separate browser profiles, owner and witness.

Checks: owner can't confirm alone; witness accepts (key made on their side); a forged signature is rejected;
a real signature checks the vow in; a signature for one vow can't be replayed on another.
Usage: python check_witness.py <app_dir>
"""
import functools
import http.server
import json
import os
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


server = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(APP)))
BASE = f"http://127.0.0.1:{server.server_address[1]}/"
threading.Thread(target=server.serve_forever, daemon=True).start()
results = {}
errors = []


def check(name, ok):
    results[name] = bool(ok)
    print(("PASS " if ok else "FAIL ") + name, flush=True)


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


with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME)
    owner_ctx = browser.new_context(viewport={"width": 390, "height": 844})
    witness_ctx = browser.new_context(viewport={"width": 390, "height": 844})
    owner = owner_ctx.new_page()
    witness = witness_ctx.new_page()
    for p in (owner, witness):
        p.set_default_timeout(20000)
        p.on("pageerror", lambda e: errors.append(str(e)))
    owner.goto(BASE)
    vid = make_vow(owner, "Run 5 km")
    other = make_vow(owner, "Write 500 words")

    # 1. owner alone: no key, no way to confirm
    v = state(owner)["vows"][0]
    check("owner state holds no signing secret", "witnessKey" not in v and v.get("witnessPub") is None)

    # 2. witness accepts in their own profile
    invite = owner.evaluate(f"witnessLink(S.vows.find(v => v.id === '{vid}'))")
    witness.goto(invite)
    witness.click("#w-accept")
    witness.wait_for_selector("#share-link")
    accept_link = witness.locator("#share-link").input_value()
    wlist = witness.evaluate("JSON.parse(localStorage.getItem('vow.witnessing'))")
    check("private key stays on witness device", len(wlist) == 1 and "d" in wlist[0]["priv"])
    check("acceptance link carries only the public key", "\"d\"" not in owner.evaluate(f"b64d('{accept_link.split('accept=')[1]}')"))
    owner.goto(accept_link)
    owner.wait_for_timeout(800)
    check("owner stores witness public key", state(owner)["vows"][0].get("witnessPub") is not None)

    # 3. forged signature is rejected
    day = owner.evaluate(f"dateKey(S.vows.find(v => v.id === '{vid}').occ[0].due)")
    forged = owner.evaluate(f"b64e(JSON.stringify({{id: '{vid}', d: '{day}', sig: bytesB64u(new Uint8Array(64).fill(7))}}))")
    owner.goto(BASE + "#ok=" + forged)
    owner.wait_for_timeout(800)
    check("forged confirmation rejected", state(owner)["vows"][0]["occ"][0]["status"] == "open")

    # 4. real signature from the witness checks the vow in
    witness.goto(BASE)
    witness.click(f"[data-confirm='{vid}']")
    witness.click("#cf button.primary")
    witness.wait_for_function("document.querySelector('#cf-link') && document.querySelector('#cf-link').value.includes('#ok=')")
    ok_link = witness.locator("#cf-link").input_value()

    # 5. replay on another vow fails (signature is bound to the vow id)
    payload = json.loads(owner.evaluate(f"b64d('{ok_link.split('ok=')[1]}')"))
    payload["id"] = other
    owner.evaluate(f"S.vows.find(v => v.id === '{other}').witnessPub = S.vows.find(v => v.id === '{vid}').witnessPub || null")
    owner.goto(accept_link.replace(vid, other))
    owner.wait_for_timeout(600)
    replay = owner.evaluate(f"b64e(JSON.stringify({json.dumps(payload)}))")
    owner.goto(BASE + "#ok=" + replay)
    owner.wait_for_timeout(800)
    check("signature can't be replayed on another vow", next(x for x in state(owner)["vows"] if x["id"] == other)["occ"][0]["status"] == "open")


    # 6. paired witness: a note check-in is only a claim until the witness signs it
    noted = make_vow(owner, "Study for 1 hour", proof="note")
    owner.goto(owner.evaluate(f"witnessLink(S.vows.find(v => v.id === '{noted}'))"))
    invite2 = owner.evaluate(f"witnessLink(S.vows.find(v => v.id === '{noted}'))")
    witness.goto(invite2)
    witness.click("#w-accept")
    witness.wait_for_selector("#share-link")
    owner.goto(witness.locator("#share-link").input_value())
    owner.wait_for_timeout(600)
    owner.goto(BASE)
    owner.click(f"[data-checkin='{noted}']")
    owner.fill("#pnote", "Read chapters 3 and 4, made flashcards")
    owner.click("#pf button.primary")
    owner.wait_for_timeout(500)
    claimed = next(x for x in state(owner)["vows"] if x["id"] == noted)["occ"][0]
    check("paired note is a claim, not kept", claimed["status"] == "open" and claimed.get("claim") is not None)
    owner.goto(ok_link)
    owner.wait_for_timeout(800)
    kept = next(x for x in state(owner)["vows"] if x["id"] == vid)["occ"][0]
    check("real witness confirmation keeps the vow", kept["status"] == "kept" and kept["proof"]["type"] == "witness")
    check("no page errors", not errors)
    print(json.dumps({"all_pass": all(results.values()), "errors": errors[:3]}), flush=True)
    os._exit(0 if all(results.values()) else 1)
