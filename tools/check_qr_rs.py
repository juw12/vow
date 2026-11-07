"""Independent QR check: read codewords back out of tools/qr.js matrices, de-interleave them and verify
every Reed-Solomon block has zero syndromes, plus decode with OpenCV where it can find the code."""
import os
from pathlib import Path

import cv2
import numpy as np
from playwright.sync_api import sync_playwright

ECC_M = [-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28]
BLOCKS_M = [-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23]
MASKS = [
    lambda x, y: (x + y) % 2 == 0,
    lambda x, y: y % 2 == 0,
    lambda x, y: x % 3 == 0,
    lambda x, y: (x + y) % 3 == 0,
    lambda x, y: (x // 3 + y // 2) % 2 == 0,
    lambda x, y: (x * y) % 2 + (x * y) % 3 == 0,
    lambda x, y: ((x * y) % 2 + (x * y) % 3) % 2 == 0,
    lambda x, y: ((x + y) % 2 + (x * y) % 3) % 2 == 0,
]

EXP = [0] * 512
LOG = [0] * 256
value = 1
for i in range(255):
    EXP[i] = value
    LOG[value] = i
    value <<= 1
    if value & 0x100:
        value ^= 0x11D
for i in range(255, 512):
    EXP[i] = EXP[i - 255]


def gf_mul(a, b):
    if a == 0 or b == 0:
        return 0
    return EXP[LOG[a] + LOG[b]]


def syndromes_zero(block, ecc_len):
    for i in range(ecc_len):
        acc = 0
        root = EXP[i]
        for byte in block:
            acc = gf_mul(acc, root) ^ byte
        if acc != 0:
            return False
    return True


def raw_modules(ver):
    result = (16 * ver + 128) * ver + 64
    if ver >= 2:
        align = ver // 7 + 2
        result -= (25 * align - 10) * align - 55
        if ver >= 7:
            result -= 36
    return result


source = Path(__file__).with_name("qr.js").read_text(encoding="utf-8")
source = source.replace("return { size, modules, version: ver };", "return { size, modules, version: ver, isFunction, mask: bestMask };")
results = []
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    page = browser.new_page()
    page.set_content("<html></html>")
    page.add_script_tag(content=source + "\nwindow.QR = QR;")
    detector = cv2.QRCodeDetector()
    for length in list(range(1, 60, 7)) + list(range(60, 760, 23)):
        text = ("https://juw12.github.io/vow/#invite=eyJpZCI6InYtMTIzIiwidCI6IlJ1biA1IGttIn0" * 12)[:length]
        r = page.evaluate("t => QR.encode(t)", text)
        ver = r["version"]
        if ver > 26:
            break
        modules = r["modules"]
        func = r["isFunction"]
        size = r["size"]
        mask = MASKS[r["mask"]]
        bits = []
        right = size - 1
        while right >= 1:
            if right == 6:
                right = 5
            for vert in range(size):
                for j in range(2):
                    x = right - j
                    upward = ((right + 1) & 2) == 0
                    y = size - 1 - vert if upward else vert
                    if not func[y][x]:
                        bits.append(int(modules[y][x]) ^ int(mask(x, y)))
            right -= 2
        raw = raw_modules(ver) // 8
        codewords = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, raw * 8, 8)]
        blocks_n = BLOCKS_M[ver]
        ecc_len = ECC_M[ver]
        short_n = blocks_n - raw % blocks_n
        short_len = raw // blocks_n
        blocks = [[] for _ in range(blocks_n)]
        k = 0
        for i in range(short_len + 1):
            for j in range(blocks_n):
                if i == short_len - ecc_len and j < short_n:
                    continue
                blocks[j].append(codewords[k])
                k += 1
        rs_ok = all(syndromes_zero(block, ecc_len) for block in blocks) and k == raw
        image = np.kron(np.where(np.pad(np.array(modules, dtype=np.uint8), 4) == 1, 0, 255).astype(np.uint8), np.ones((6, 6), np.uint8))
        decoded = detector.detectAndDecode(image)[0]
        decode_note = "decoded" if decoded == text else ("not found" if decoded == "" else "WRONG")
        ok = rs_ok and decode_note != "WRONG"
        results.append(ok)
        print(("PASS" if ok else "FAIL"), f"len={length:4d} v={ver:2d} rs={'ok' if rs_ok else 'BAD'} opencv={decode_note}", flush=True)
    browser.close()
print("all_pass" if all(results) else "FAILED", flush=True)
os._exit(0 if all(results) else 1)
