# Vow

Keep the promises you make to yourself. Put a stake on a promise, name a witness (or go solo), show proof before the deadline.
If you miss it, Vow records the debt and you pay your chosen cause yourself, in full.

Built as a free alternative to Forfeit (forfeit.app), which charges a subscription and keeps forfeited stakes.
Live: https://juw12.github.io/vow/

## Get it on your device

- **Windows:** [`Vow-Windows-Setup.exe`](https://github.com/juw12/vow/releases/download/desktop/Vow-Windows-Setup.exe) (no admin needed; if Windows says it protected your PC, choose *More info → Run anyway*), or without installing [`Vow-Windows-Portable.zip`](https://github.com/juw12/vow/releases/download/desktop/Vow-Windows-Portable.zip).
- **Mac:** [`Vow-macOS-AppleSilicon.dmg`](https://github.com/juw12/vow/releases/download/desktop/Vow-macOS-AppleSilicon.dmg) (M1 and newer) or [`Vow-macOS-Intel.dmg`](https://github.com/juw12/vow/releases/download/desktop/Vow-macOS-Intel.dmg). The first time, macOS blocks it because it is not notarized: **System Settings → Privacy & Security → Open Anyway**.
- **Android:** [`Vow-android.apk`](https://github.com/juw12/vow/releases/download/android/Vow-android.apk): open the file on the phone and allow your browser to install apps once.
- **iPhone:** open https://juw12.github.io/vow/ in Safari, tap Share, then **Add to Home Screen**.

The Windows, Mac and Android apps are the web app in its own window ([`desktop/`](desktop/README.md), [`android/`](android/README.md)) and change with it. Each build is opened on GitHub's machines before it is published: on Windows and on a Mac the page loads, the app starts and can store data; on an Android emulator it installs, opens and stays up. They are not code-signed or notarised, and no real phone or PC has run them yet.

## What it does
- Once or repeating vows (days of the week, 1 week / 30 days / 66 days / no end).
- Proof by photo (taken live with the camera inside Vow - no gallery uploads - and time-stamped), written note,
  focus timer, or your witness's word. No camera? A photo vow can take a written note instead (or retry the camera), and the record says so.
- **Solo or witnessed.** Leave the witness empty for a solo vow that runs on your word; add a witness later from the card.
- **Change proof type** after sealing; like every easing change it waits 24 hours.
- **Witnesses hold the key.** Send your witness an invite link. When they open it in Vow, their device creates a
  private signing key (ECDSA P-256) that never leaves it, and they send back an acceptance link with the public key only.
  From then on your photos, notes and timers are claims: a check-in counts only when your witness signs it.
  They get 24 hours after the deadline to sign. By default a claim counts if they stay silent that long
  (switch it off in Fine-tune for strict vows). Forged or replayed confirmations are rejected.
- Deadline passes without proof: the vow breaks automatically, the stake goes into an "owed" ledger and a confession
  message for your witness is drafted, with a link the witness opens to track the debt on their own phone and
  confirm the payment later. Debts older than 7 days block new vows until they are cleared.
- **Debts need proof.** A debt clears only with a photo of the donation receipt, or with a confirmation link your
  witness signs on their own device ("paid:<debt>"). Ticking "I paid" alone is not enough.
- Raising a stake is instant. Lowering, delaying or deleting waits 24 hours, and a deadline before then still counts.
- **No free escape from far deadlines.** If the next deadline is more than 24 hours away, deleting means walking away:
  you owe the stake, or your witness signs you off.
- **QR hand-offs.** Every link you pass between phones (invite, acceptance, proof confirmation, walk-away, payment
  request and confirmation) is also shown as a QR code, so your witness can scan it from your screen.
- **Honest focus timer.** The timer counts real elapsed time; leaving Vow for more than 15 seconds restarts the session.
- "Excuse one deadline": one per 30 days, only before the deadline. With an accepted witness the excuse is a signed
  request ("pass:<check-in>") they approve; until then the deadline stands, with 24 hours extra for their answer.
- Optional escalation: stake x1.5 per miss, capped at 4x.
- Streaks, per-vow history dots, 12-week heatmap, monthly summary, calendar (.ics) reminders, light/dark theme.
- Export/import backup, including the signing keys for vows you witness. Erasing keeps unpaid debts.

## Design
The UI follows `design.md` ("refined paper": cream paper, serif headings, one brick-red accent, no purple, no emoji),
chosen by a judged 4-direction bracket (`hone/design-bracket.md`). On desktop it runs as an app shell with a
left sidebar; on phones it keeps the bottom tab bar.

## Honest limits
- Vow never touches money. It cannot charge you; your witness is what makes it real.
- No server. Solo vows, and vows whose witness hasn't accepted yet, run on your honor.
- Data lives in this browser only (localStorage). Export backups.

## Run
Open https://juw12.github.io/vow/ and install it from the browser menu, or serve this folder yourself
(needed for offline install and shareable links): `python -m http.server 8080`, then open http://localhost:8080.

Checked by `tools/check.py` (10 Playwright gates), `tools/check_witness.py` (two-device signed-witness test) and
`tools/check_backup.py`, `tools/check_proof.py` (camera-only photos, receipt / witness-signed debt clearing) and
`tools/check_extras.py` (24h walk-away, wall-clock timer, QR decode, payment QR flow) and `tools/check_v10.py`
(solo vows, note instead of photo, witness response window, witness-tracked debts, signed passes, proof changes); scored by a 3-model council against `hone/rubric.md` (log in `hone/refine_log.md`).
MIT licence.
