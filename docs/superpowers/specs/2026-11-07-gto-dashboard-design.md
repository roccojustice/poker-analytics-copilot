# GTO comparison dashboard — design

*Session 72, 2026-11-07. First M8 dashboard. Status: approved by the user (line list as drafted,
adjusted on the way if needed).*

## Intent

The user has built a second PT4 database of hands played **bot vs bot**, both bots playing GTO
from 6-max ranges. The dashboard puts the user's frequencies next to the bots' for the same
spot, line by line, under the same board / hand / draw / sizing filters Spotlight already has.
The goal is to find the gaps ("I cbet low flops 40%, GTO 62%; the gap is in my overpairs")
and close them over time.

This replaces SPEC's M8 wording ("one dashboard per line, 20 total"). M8 becomes: **one
dashboard per spot, comparing the user's frequencies with GTO's**, each spot's line list
defined by the user. SPEC is updated when this design is approved.

## Goals

1. A **Dashboards page**, separate from the hands page. Nav between the two (Manos |
   Dashboards). The two are never mixed on one page.
2. First dashboard: **`2bp ip pfr`**.
3. **Level 1, the spot view:** board filters on top (Flop / Turn / River types, the same ones
   as the hands page), then the spot's **list of lines**. Each row: line name, the user's
   frequency, GTO's frequency, the gap, and each side's hand count.
4. **Level 2, a line's detail** (click a row): hand type × action and draw type × action
   tables, **user and GTO side by side**, plus the hands of each side. Hand / draw picks work as
   on the hands page and apply to both sides at once.
5. **Sizing, in both senses:**
   - **What Hero bets:** a bet line's `B` splits into `Bs / Bm / Bl / Bo`, both sides, in
     level 1 and level 2.
   - **What Hero faces:** an S / M / L / O filter for lines where Hero faces a bet (vs probe,
     vs XR, …), so the frequency vs a small and vs a large bet are not pooled.

## Non-goals (this design)

- Other spots' dashboards. Each comes later, its line list defined by the user.
- **`2bp oop pfc` and any spot played by the GTO DB's `Villain` bot.** Its hole cards are known
  only at showdown (826,858 of 1.5M hands, 55%), so hand / draw filters on that side would be
  biased toward showdown hands. Needs the bot hands regenerated with both hands visible, or a
  decision on how to live with it. Out of scope here.
- Charts. Numbers, as on the hands page.
- Recommending how to play. The page shows the gap; the user decides what to do about it.
- The replayer (parked, Session 72).

## Anti-goals (would make it a failure even if it works)

- **Apples vs oranges:** comparing the user's CO/MP opens against a BTN GTO range. The gap
  would come from preflop, not from postflop play.
- **A gap without its sample size.** 40% vs 55% on 12 hands is noise; the counts must be visible.
- **A number that silently disagrees with the hands page.** The user side of every row must
  equal what Spotlight's hands page returns for the same Line + filters.

## The data (recon, Session 72)

GTO DB: PT4 database `PT4_2026_11_07_184219`, same server/credentials as the user's DB.

- 1,500,000 hands, PokerStars format, 6-max tables (`cnt_players = 6`, normal 6-max position
  codes), 100.5 BB stacks, dates 2026-10-14 → 2026-10-21.
- Players `Player1/2/3/5` are filler: never VPIP, fold every hand.
- **Every hand is the same spot:** bot `Hero` = BTN, opens (`cnt_p_raise = 1`); bot `Villain` =
  BB, calls. Heads-up flop in 100% of hands. No 3-bets.
- `Hero` bot's hole cards are known in every hand; `Villain` bot's only at showdown (55%).

Consequences:
- For `2bp ip pfr`, the GTO side is the `Hero` bot.
- **The user's side is locked to formation `BB vs BTN`** (the only formation the bots play).
  Shown in the filter line so the user sees it.
- Raw history text is available (`cash_hand_histories`); not needed for this design.

## How it works (decided)

- **A line = a Spotlight Line + its measured action.** The dashboard row name is in Hero's
  terms (cbet, double barrel…); under the hood it is a villain-grammar Line that `parse_line`
  accepts. The frequency shown is the measured distribution over the same set the hands page
  measures (`{B, X}` or `{F, C, R}`).
- **Both sides go through the same pipeline** (`parse_line` → `build_spot_query` →
  classification → distribution / splits). Only the database and the player differ. No second
  implementation of any filter.
- **Lines are config, not code**, like the hands page's `spot-config`: a registry per spot
  (name, Line, which action(s) the row headlines). Adding a line = adding an entry.

### Line list for `2bp ip pfr` (approved; changes as the user studies with it)

| Row name | Line (villain grammar) | Measured | Headline |
|---|---|---|---|
| Cbet flop | `X` | B / X | B (+ Bs…Bo) |
| Double barrel | `XC-X` | B / X | B (+ Bs…Bo) |
| Triple barrel | `XC-XC-X` | B / X | B (+ Bs…Bo) |
| vs XR flop | `XR` | F / C / R | F, C, R |
| vs probe turn | `X-B` | F / C / R | F, C, R |
| Delayed cbet turn | `X-X` | B / X | B (+ Bs…Bo) |
| vs XR-B (called XR, villain bets turn) | `XR-B` | F / C / R | F, C, R |
| vs turn donk (villain called the cbet, leads turn) | `XC-D` | F / C / R | F, C, R |

Every Line in the final list must pass `parse_line` for `2bp ip pfr`
(a test, like `tests/test_static_config.py`). All Lines in the draft above parse today
(checked Session 72); `XC-B` does not (`B` in a donk's place errors, it is `XC-D`).

## Left to the builder (with the builder's calls marked)

- **DB access:** a second engine for the GTO DB (env `GTO_POSTGRES_DB`, `GTO_HERO_NAME=Hero`),
  and `db` query functions taking the engine + player id instead of assuming the user's. Same
  parameter-binding rules. *Builder's call: player resolved by name per DB, cached, fail loud
  unless exactly one row, as `hero_id()` does now.*
- **Performance.** The GTO side is ~1.5M hands; classifying hand / draw / board types in Python
  per request will be slow. *Builder's call:* precompute per-hand board / hand / draw types for
  the GTO DB once into a **local cache file** (outside PT4; never write into a PT4 database),
  invalidated when the DB's hand count changes. No sampling: the GTO numbers are exact.
  Target: a dashboard refresh in a few seconds.
- **Runout filters vs a line's street.** A turn filter means nothing for a flop line. *Builder's
  call:* rows whose decision street is earlier than a selected runout filter show "—" with a
  tooltip, instead of the hands page's error.
- **Faced-size filter.** *Builder's call:* one S / M / L / O multi-select at the top of the
  dashboard; it applies to rows where Hero faces a bet and is ignored (greyed) for bet rows.
  Level 2 also shows the faced-size split table, both sides, as the hands page's `split` does.
- **Level 2 layout.** *Builder's call:* its own view on the Dashboards page with a ← Back that
  restores level 1 and its filters; not a pop-up (the tables are wide). User and GTO cells
  side by side in one table (`yours | GTO` per action), not two separate tables.
- **GTO hand list.** Can be hundreds of thousands. *Builder's call:* show the first N
  (e.g. 200) of the filtered set with the total count; the user's list in full, as now.
- **Gap column:** user − GTO, in points, per headline action.
- **Date range** (From / To) applies to the user's side only, so the user can see whether a gap
  closes over time. *Builder's call.*

## Validation

- **User side:** each row equals the hands page for the same Line + `BB vs BTN` + filters
  (exact hand set, not a count) — a `db` test over the line list.
- **GTO side, preflop:** `2bp ip pfr` returns exactly the `Hero` bot's 1.5M hands; `2bp oop pfc`
  returns exactly the `Villain` bot's. Exact sets.
- **GTO side, one line vs PT4:** one PT4 hand-list export from the GTO DB (e.g. cbet flop)
  diffed with `pt4_diff.py`, 0/0, before the numbers are trusted.
- Hand / draw / board classification is already validated (Sessions 62–67); it only has to run
  on the other DB.

## Open (needs the user)

- None. The user's "vs X-B" is read as the turn probe (`X-B`); the turn donk is `XC-D`.
