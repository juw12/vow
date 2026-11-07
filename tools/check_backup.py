"""Check that a backup carries the witness signing keys (vow.witnessing) and import restores them.

Usage: python check_backup.py <app_dir>
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

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(APP))
handler.log_message = lambda *args: None
server = socketserver.TCPServer(("127.0.0.1", 0), handler)
BASE = f"http://127.0.0.1:{server.server_address[1]}/"
threading.Thread(target=server.serve_forever, daemon=True).start()

FAKE_WITNESSING = [{"id": "v-test", "title": "Run 5 km", "owner": "Alex", "priv": {"kty": "EC"}}]
failures = []

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME)
    ctx = browser.new_context(accept_downloads=True)
    page = ctx.new_page()
    page.set_default_timeout(20000)
    page.on("pageerror", lambda e: failures.append(f"pageerror: {e}"))
    page.goto(BASE)
    page.wait_for_selector("#view")
    page.evaluate("list => localStorage.setItem('vow.witnessing', JSON.stringify(list))", FAKE_WITNESSING)
    page.goto(BASE + "#settings")
    with page.expect_download() as download:
        page.click("#export")
    backup = json.loads(Path(download.value.path()).read_text(encoding="utf-8"))
    has_keys = backup.get("witnessing") == FAKE_WITNESSING
    page.evaluate("localStorage.removeItem('vow.witnessing')")
    page.set_input_files("#import-file", files=[{
        "name": "b.json",
        "mimeType": "application/json",
        "buffer": json.dumps(backup).encode(),
    }])
    page.wait_for_timeout(500)
    restored = page.evaluate("JSON.parse(localStorage.getItem('vow.witnessing') || '[]')")
    state_clean = "witnessing" not in page.evaluate("JSON.parse(localStorage.getItem('vow.v1'))")
    browser.close()

checks = {
    "export includes witness keys": has_keys,
    "import restores witness keys": restored == FAKE_WITNESSING,
    "keys not duplicated into vow state": state_clean,
    "no page errors": not failures,
}
for name, ok in checks.items():
    print(("PASS " if ok else "FAIL ") + name, flush=True)
print(failures)
os._exit(0 if all(checks.values()) else 1)
