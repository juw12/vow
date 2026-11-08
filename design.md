# Vow design system ("refined paper", v4)

Read this before changing any UI in `index.html`. The code must match these tokens.
Chosen by a judged 4-direction bracket (see `hone/design/bracket/bracket.md`): D "refined paper" beat
C "dashboard" 3-0 and B "bank app" 3-0. Judges cited the serif/sans pairing, the cream and brick-red palette
and the ruled ledger row as what makes it specific to Vow.

## Facts the design serves
- Who: one person keeping a promise to themselves, with a friend as witness.
- One job per screen: home = what is due and how to check in; new = seal a vow; history = your record.
- Real numbers on screen: stake, time left, kept count and rate, money owed.

## References (what each one gave)
| Reference | Taken |
|---|---|
| Printed contracts and letterpress stationery | Cream paper, serif headings, a wax-seal mark, ruled lines instead of boxes |
| Bank statement header | The ledger strip: one ruled row of tabular numbers with uppercase micro-labels |
| Things 3 | Restraint: one accent, hairline borders, no decorative chrome or shadows |
| Monzo | Money stated plainly in red; numbers set large and tabular |

## Palette
| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | `#f7f3ea` | `#15120e` | page |
| `--card` | `#fffdf9` | `#201c17` | cards, 1 px border, no shadow |
| `--ink` | `#1d1a16` | `#f2ebdd` | text (15.7:1 on bg) |
| `--muted` | `#645b50` | `#b3a895` | secondary text (6.0:1 on bg, 6.6:1 on card) |
| `--line` | `#e2d9c8` | `#3a332a` | hairlines and borders |
| `--soft` | `#f0e9dc` | `#2a251e` | selected tab, quiet fills |
| `--seal` | `#a8261b` | `#f05a47` | the one accent: primary button, stake, debts (7.0:1 on card; white on seal 7.1:1) |
| `--kept` | `#1d6b3a` | `#4cc477` | kept / accepted only (6.4:1) |
| `--warn` | `#8a4f0c` | `#f0a640` | waiting / pending only (6.5:1) |

No purple, indigo or violet. No gradients. One accent per screen.

## Type
- Headings, wordmark, big numbers: serif stack `"Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif`.
- Body and UI: `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`, 16 px / 1.5.
- H1 32 px (28 px under 560 px), H2 22 px, card title 20 px serif.
- Numbers: `font-variant-numeric: lining-nums tabular-nums`.
- Micro-labels: 11.5 px uppercase, letter-spacing .08 em, muted.

## Spacing, radius, elevation, motion
- Spacing: 4, 8, 10, 14, 18, 28 px (`.stack` gap 14 px, card padding 18 px).
- Radius: 12 px cards, 10 px buttons, 999 px chips only.
- Elevation: none. Borders separate surfaces. Dialogs are the only shadowed layer.
- Motion: 150 ms ease on press and the "More options" chevron; the seal stamp only after a kept vow;
  all motion off under `prefers-reduced-motion`.

## Signature
The **ledger strip**: your record (kept, kept rate, streak, stakes kept safe) as a ruled row under a 2 px ink rule,
like a statement header. The wax-seal mark appears only in the header and on success.

## Components
- Chips are outlines (1 px border, no fill). Stake chip uses the seal colour for text and border. Status chips use
  kept or warn. The witness is one chip: "Witness: Sam, accepted", or a warn chip that is also the invite button.
- Primary button: solid seal, white text. At most one per card ("Check in") and one in the screen header ("New vow").
- Debt card: 3 px seal top rule on a plain card, never a filled red box.
- "More options" is a disclosure with a chevron that turns when open.
- QR codes: white tile, 4-module quiet zone, max 220 px wide, labelled for screen readers.

## Voice
Plain and direct, second person, says what happens and when ("It applies in 24 hours").
Banned words: supercharge, seamless, unlock, next-level, effortless, magic, revolutionary, journey.

## Banned defaults
- Purple/indigo gradients, gradient text, glow blobs, glassmorphism.
- Emoji anywhere in the UI (headings, buttons, chips, lists, toasts).
- Inter or one default sans for everything including headings and brand.
- Filled pastel chips for every attribute; identical shadowed cards in a grid.
- Centred-everything layouts, fake testimonials or logos, stock 3D blobs.
- "Get started" as the only call to action.

## v7 additions (professional polish, 2026-11-08)
- **Icons**: line SVG only (`.ic`, 1.8 stroke, currentColor). No emoji or arrow glyphs anywhere in the UI.
- **Navigation**: header links with icon + label on tablet/desktop; below 640 px a fixed bottom tab bar
  (3 equal tabs, 52 px targets, active tab in seal colour).
- **Layout**: Home, History and Settings use `.layout` = `.main` + `aside.side`. At 1024 px+ the wrap is
  1080 px with a 1fr / 340 px grid and a sticky side column; single-column views stay at 760 px.
- **Vow card meta** (`dl.meta`): Stake / Proof / Witness as a ruled 3-column grid (2 + 1 on phone);
  uppercase 11.5 px labels, 14.5 px values, stake amount in seal.
- **More options** (`.menu`): a bordered list of `.menu-item` rows; "Delete vow" sits apart at the
  bottom in seal, separated by a 6 px band. Delete and Erase still require typing DELETE / ERASE.
- **Danger zone**: Settings has its own "Erase data" card with seal heading and border.
- **New vow**: idea chips under "I will", one "Deadline, stake and proof" summary tile with "Change",
  and a "What happens next" steps card in the side column.
- **History**: story sentence in the hero; heatmap with fluid cells and a swatch legend in the side column.
- **Check-in (photo)**: 4:3 camera frame with a "Camera preview" placeholder, full-width Take photo.
- Tried and not kept (council ties): 40 px owed amount, quiet record band, inline meta, grouped menu,
  secondary Check in when the deadline is far. See `hone/refine_log.md`.

## v8 additions (one focus on Home, 2026-11-08)
- **Home order**: a "Next up" lead card (soonest deadline, primary Check in, seal-tinted border); other vows
  use a secondary outlined Check in. Vows are sorted by deadline. Below 1024 px the vow list comes first.
- **Hero line**: "2 active · next deadline in 9h 03m · $10 owed" - the debt is named once, up top, as a link.
- **Debt notice** (`.owed-note`): a slim card with an eyebrow "You owe $10", one row per debt, I paid, and one
  short line of help. No headline competing with the vow card.
- **Record band** (`.record`): ruled 4-up stats (2 x 2 on phone and in the side column), sentence-case
  labels; History "Totals" uses the same component.
- **New vow**: numbered steps 1 I will, 2 Witness, 3 Deadline, stake and proof.
- **More options**: grouped with small headers ("Change the vow", "Share"); Delete stays apart at the bottom.
- **Settings**: the explainer keeps its first paragraph; money, witnesses and privacy fold into a disclosure.
- **Photo check-in**: Submit proof is disabled until a photo is taken.
- Secondary button style (`.btn.secondary`): card background, ink text, 1 px ink-tinted border.
- Tried and not kept (council): side-column calendar on desktop Home, quieter owed label + I paid on its own
  row, ink-only money amounts with a countdown lockup. See `hone/refine_log.md`.
