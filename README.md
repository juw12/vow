# Vow

Keep the promises you make to yourself. Put a stake on a promise, name a witness, show proof before the deadline.
If you miss it, Vow records the debt and you pay your chosen cause yourself, in full.

Built as a free alternative to Forfeit (forfeit.app), which charges a subscription and keeps forfeited stakes.
Live: https://juw12.github.io/vow/

## What it does
- Once or repeating vows (days of the week, 1 week / 30 days / 66 days / no end).
- Proof by photo (taken live with the camera inside Vow - no gallery uploads - and time-stamped), written note,
  focus timer, or your witness's word.
- **Witnesses hold the key.** Send your witness an invite link. When they open it in Vow, their device creates a
  private signing key (ECDSA P-256) that never leaves it, and they send back an acceptance link with the public key only.
  From then on your photos, notes and timers are claims: a check-in counts only when your witness signs it.
  They get 24 hours after the deadline to sign. Forged or replayed confirmations are rejected.
- Deadline passes without proof: the vow breaks automatically, the stake goes into an "owed" ledger and a confession
  message for your witness is drafted. Debts older than 7 days block new vows until they are cleared.
- **Debts need proof.** A debt clears only with a photo of the donation receipt, or with a confirmation link your
  witness signs on their own device ("paid:<debt>"). Ticking "I paid" alone is not enough.
- Raising a stake is instant. Lowering, delaying or deleting waits 24 hours, and a deadline before then still counts.
- One "life happens" pass per 30 days, only before the deadline.
- Optional escalation: stake x1.5 per miss, capped at 4x.
- Streaks, per-vow history dots, 12-week heatmap, monthly summary, calendar (.ics) reminders, light/dark theme.
- Export/import backup, including the signing keys for vows you witness. Erasing keeps unpaid debts.

## Honest limits
- Vow never touches money. It cannot charge you; your witness is what makes it real.
- No server. Until your witness accepts the invite, proof is on your honor.
- Data lives in this browser only (localStorage). Export backups.

## Run
Open https://juw12.github.io/vow/ and install it from the browser menu, or serve this folder yourself
(needed for offline install and shareable links): `python -m http.server 8080`, then open http://localhost:8080.

Checked by `tools/check.py` (10 Playwright gates), `tools/check_witness.py` (two-device signed-witness test) and
`tools/check_backup.py` and `tools/check_proof.py` (camera-only photos, receipt / witness-signed debt clearing); scored by a 3-model council against `hone/rubric.md` (log in `hone/refine_log.md`).
MIT licence.
