| time | mode | result | detail | judges |
|---|---|---|---|---|
| 2026-11-07 16:52 | council score | 7.45 | split: C2 | Pega-Vision=6.6, Pega-Thinking=8.95, GLM-5.3-Flash=7.45 |
| 2026-11-07 17:16 | council pair | B wins: True | votes A/B/tie 0/3/0 | council-judged (3 judges) |
| 2026-11-07 17:16 | council score | 8.4 | split: - | Pega-Vision=8.35, Pega-Thinking=8.65, GLM-5.3-Flash=8.15 |
| 2026-11-07 17:16 | council score | 9.1 | split: - | Pega-Vision=8.25, Pega-Thinking=9.1, GLM-5.3-Flash=9.1 |


## Vow rounds (rubric v1)

| round | change | gates | judge score | pairwise win | kept? | note |
|---|---|---|---|---|---|---|
| v0 | baseline: stake, auto-break, 24 h easing lock, grace pass, witness code, .ics, offline PWA | 10/10 | 7.45 (old shots) / 8.40 (clean shots) | - | baseline | first scoring used screenshots with a sticky-header capture artifact; re-scored for a fair comparison |
| 1 | [hidden] bug fix; free-edit = wording only; witness required + "not sent yet" nudge; code revealed only after "I saw proof"; per-vow streak dots; month story + best streak; milestone toasts; shorter form | 10/10 | 9.10 | 3-0 (both orders) | yes | done: gates pass and 9.10 >= 8.5 |

Stop reason: done (all gates pass, council 9.10 >= 8.5). Label: council-judged (3 judges: Pega-Vision, Pega-Thinking, GLM-5.3-Flash).
Open council fixes (not done): witness-held secret so the owner cannot mint codes; receipt photo / witness confirm to clear debts; camera-only fresh capture instead of file.lastModified; calendar heatmap; required fields at top of form.
| 2026-11-07 17:44 | council score | 9.1 | split: - | Pega-Vision=8.07, Pega-Thinking=9.1, GLM-5.3-Flash=9.1 |
| 2026-11-07 17:46 | council pair | B wins: True | votes A/B/tie 0/3/0 | council-judged (3 judges) |
| 2026-11-07 18:15 | council score | 8.8 | split: - | Pega-Vision=8.15, Pega-Thinking=8.65, GLM-5.3-Flash=9.05 |
| 2026-11-07 18:17 | council pair | B wins: True | votes A/B/tie 0/3/0 | council-judged (3 judges) |

## Vow rounds 2-3 (rubric v1, best = v1 at 9.10)

| round | change | gates | judge score | pairwise vs v1 | kept? | note |
|---|---|---|---|---|---|---|
| 2 | witness-held ECDSA P-256 keys (owner can no longer mint confirmations), signed `#ok=` links, "You're a witness for" list, share drafts after pass/payment, 12-week heatmap, witness field first | 10/10 + witness e2e 8/8 | 9.10 | 3-0 | no (tie, needs >= 9.40) | stall 1 |
| 3 | paired witness turns photo/note/timer into a claim that needs a signature (24 h grace after deadline); erase keeps unpaid debts; defaults folded into one summary line; "Send invite" pill; hashchange closes open dialog (bug); duplicate id fixed | 10/10 + witness e2e 9/9 | 8.80 (judges 8.15-9.05) | 3-0 | no (below 9.10) | stall 2 -> stop |

Stop reason: 2 rounds without a kept gain (rule). Scored best stays v1 at 9.10, council-judged (3 judges).
Ship decision: v3 + one post-loop bug fix is what's live. Reason: it fixes objective defects that v1 has
(owner-forgeable witness confirmations, dialog left open on navigation, duplicate id, witness keys missing
from backups) and won head-to-head against v1 3-0 twice (v2 and v3). Its absolute council score (8.80) is
lower than v1's (9.10); the judges' totals spread 0.9 points on the same build, so the absolute
score is noisier than the pairwise vote. This is a deliberate deviation from the strict keep rule, reported as such.
Post-loop fix (objective, tested by tools/check_backup.py): backups now include the witness signing keys
(`vow.witnessing`) and import restores them; erase text says witnessed vows keep working.
Open council fixes (not done): delete of a far-off vow is cost-free (tell/ask witness); timer pauses on
tab switch; witness onboarding friction (QR/one-tap); EXIF capture-time check; witness counter-sign for
"I paid" receipts.
