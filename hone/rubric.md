# Vow - rubric v1 (frozen 2026-11-07)

Goal: a commitment app that beats Forfeit (forfeit.app) for a person who wants to actually keep promises,
free forever, no account, no company holding the money.

Known Forfeit facts (web search 2026-11-07): stake money per task, lose it if no proof by deadline;
proof via AI-checked photos, human-reviewed timelapses, GPS, health data; human appeals within ~12 h unless
Hard Mode; subscription ~$10.99/month; forfeited money is kept by the company; complaints about the paid-only
model, verification delays and strangers seeing personal photos.

## Hard gates (code checker, Playwright; all must pass)

- G1 Zero console errors / page errors through the whole test flow.
- G2 Create a vow -> check in with proof before the deadline -> vow is KEPT.
- G3 Deadline passes with no proof -> vow is BROKEN automatically, stake lands in the "owed" ledger,
     a confession message to the witness is drafted.
- G4 Easing changes (lower stake, push deadline, delete) are delayed 24 h; raising the stake is immediate.
- G5 Grace pass ("life happens") only works BEFORE the deadline, max 1 per 30 days.
- G6 Data survives reload; export -> wipe -> import restores everything.
- G7 No horizontal overflow at 320, 390, 768, 1024, 1440 px, light and dark theme.
- G8 No requests to any other origin; service worker registers; manifest is valid (installable).
- G9 Every button, link and input has an accessible name.
- G10 Calendar export (.ics) is valid and contains a VALARM reminder.

## Soft criteria (council-judged)

- C1 Commitment strength (w=0.30): 4 = the stake is just a number you can quietly edit or delete; 7 = failures are recorded and visible and there is some friction against backing out; 10 = backing out is genuinely costly: easing changes are delayed, failure is detected automatically at the deadline, the debt stays visible until settled with proof, a human witness is involved and excuses must be declared in advance.
- C2 Ease and clarity (w=0.25): 4 = many fields, jargon, unclear next step; 7 = a first vow in under a minute, clear labels; 10 = a first vow in about 30 seconds thanks to smart defaults, every screen has one obvious next action, plain words.
- C3 Visual polish (w=0.20): 4 = default-looking form; 7 = consistent, clean hierarchy, both themes work; 10 = distinctive and crafted, purposeful micro-interactions, excellent on phone and desktop.
- C4 Motivation and feedback (w=0.15): 4 = just a list; 7 = stats and streaks; 10 = progress that makes you want to continue, clear money kept vs owed, a history that tells a story.
- C5 Trust and honesty (w=0.10): 4 = unclear where data or money goes; 7 = clear privacy and money statements; 10 = fully transparent, no account, export, limitations stated honestly (e.g. it cannot charge you; it relies on your witness).

Done = all gates pass AND council score >= 8.5. Max 5 rounds, stop after 2 rounds without a kept gain.
Keep a candidate only if council score >= best + 0.3 AND it wins the swapped-order pairwise vote.
