# Vow

Keep the promises you make to yourself. Put a stake on a promise, name a witness, show proof before the deadline.
If you miss it, Vow records the debt and you pay your chosen cause yourself, in full.

Built as a free alternative to Forfeit (forfeit.app), which charges a subscription and keeps forfeited stakes.

## What it does
- Once or repeating vows (days of the week, 1 week / 30 days / 66 days / no end).
- Proof by photo (time-stamped, must be under 30 minutes old), written note, focus timer, or a code from your witness.
- Deadline passes without proof: the vow breaks automatically, the stake goes into an "owed" ledger and a confession
  message for your witness is drafted. Debts older than 7 days block new vows until you log a receipt.
- Raising a stake is instant. Lowering, delaying or deleting waits 24 hours, and a deadline before then still counts.
- One "life happens" pass per 30 days, only before the deadline.
- Optional escalation: stake x1.5 per miss, capped at 4x.
- Streaks, per-vow history dots, monthly summary, export/import backup, calendar (.ics) reminders, light/dark theme.

## Honest limits
- Vow never touches money. It cannot charge you; your witness is what makes it real.
- No server: you could open your own witness link or lie in a note. Vow makes cheating deliberate, not easy.
- Data lives in this browser only (localStorage). Export backups.

## Run
Open `index.html` in a browser, or serve the folder (needed for offline install and shareable witness links):
`python -m http.server 8080` then open http://localhost:8080.

Live: https://juw12.github.io/vow/

Checked by `python tools/check.py . shots` (10 Playwright gates) and scored by a 3-model council against `hone/rubric.md`.
MIT licence.
