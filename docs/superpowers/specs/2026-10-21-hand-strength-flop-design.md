# Hand strength on the flop (M7 #7, part 1) — Design

*Session 64, 2026-10-21. Brainstormed with the user. Reuses the shape of the flop type and
runout filters (`2026-10-18-flop-type-design.md`, `2026-10-19-runout-types-design.md`) and
the facing split table (`2026-10-17-facing-split-design.md`).*

## Problem

The user studies how they play each class of hand in a spot: do they bet top pair, check
second pair, give up with air? PT4 can filter by hand, but its categories are **absolute**
(best five cards, board included): Kh9s on JsJd9h counts as "two pair" there, although the
user only holds second pair. Filtering PT4 by hand strength is also slow to set up. The user
wants both a **filter** (keep only some hand classes) and a **breakdown** (every class at once,
each with its action frequencies), shown as a table like their GTO Wizard / PT4 screenshots
but in Spotlight's number-table style.

## Scope of part 1 and the ladder

M7 #7 is cut in parts, each validated before the next:

1. **This document: made hands at a flop decision.** Base categories only.
2. Made hands on turn and river decisions (adds `4th pair`, board-played straights/flushes).
3. Subcategories: Flush (nut, 2nd nut, 3rd nut…), Set, Two pair. Defined one by one with
   the user.
4. Draws (Combo draw, Flush draw nuts, Flush draw, OESD, Gutshot, BDFD 2 cards, BDFD 1 card,
   BDSD, No draw), a second independent dimension. A hand appears in both dimensions (6h5h on
   KhQh6s is 3rd pair **and** a flush draw).

Kickers are out of scope for now (Kh9s on JJ9 is 2nd pair; its K kicker is not a filter).

## Solution in one paragraph

When the Line's decision is on the **flop**, Spotlight labels every matching hand with
**exactly one** hand type from Hero's two hole cards and the three flop cards. A multi-select
**Hand** control on the bar keeps only the checked types (OR within the control, AND with
every other control). The result gains a **hand breakdown table**: one row per hand type
present, its hand count and share of the result, and one column per action with % and count;
cells select hands in the hand list, like the facing split. The hand list gains a
**Hand type** column. With a turn or river decision the control is disabled and no breakdown
is computed.

## The hand types (the user's definitions)

Exclusive, assigned by **priority, top to bottom**: a hand gets the first type it qualifies
for. This is also the page order and the breakdown row order.

Terms: a hole card **pairs** a board rank when they have the same rank. The board's
**distinct ranks**, sorted high to low, are its positions 1, 2, 3 (a paired flop has two
positions). A board-only pair or board trips is never Hero's hand by itself.

| # | Type | Rule on the flop |
|---|---|---|
| 1 | Straight flush | Best five cards are a straight flush (needs both hole cards) |
| 2 | Quads | Four of a kind using a hole card: pocket pair + board pair of that rank, or one hole card + board trips of that rank |
| 3 | Full house | Best five cards are a full house using a hole card: e.g. AA on 555, 99 on JJ9, K9 on KK9, T5 on T55 |
| 4 | Flush | Five of one suit (on the flop: both hole cards + a monotone flop of that suit) |
| 5 | Straight | Five consecutive ranks using hole cards (A plays high and low) |
| 6 | Set | Pocket pair matching one board rank |
| 7 | Trips | One hole card matching a paired board rank (A5 on T55) |
| 8 | Two pair | **Each** hole card pairs a **different** board rank (JT on TJ3, AT on T5A, 98 on 98K) |
| 9 | Overpair | Pocket pair above every board rank |
| 10 | Top pair | A hole card pairs position 1 |
| 11 | 2nd pair | A hole card pairs position 2, **or** a pocket pair with exactly one distinct board rank above it **and at least one below** |
| 12 | 3rd pair | A hole card pairs position 3, **or** a pocket pair with exactly two distinct board ranks above it **and at least one below** (only possible on a flop with three distinct ranks) |
| 13 | Underpair | Pocket pair below every board rank (checked on the pocket pair before 2nd/3rd pair: 77 on JJ9 is Underpair, not 3rd pair) |
| 14 | Ace high | None of the above and Hero holds an Ace |
| 15 | No made hand | None of the above |

`Straight flush` is the assistant's addition (the user's list stops at Quads; it is rare and
needs a home). Its row hides when empty, like any other.

User-confirmed examples (test fixtures, exact type):

| Hole | Flop | Type | Why |
|---|---|---|---|
| Kh9s | JsJd9h | 2nd pair | Distinct ranks J, 9; the 9 is position 2. Board JJ is not Hero's |
| TT | JJ9 | 2nd pair | One distinct rank (J) above |
| 77 (also 88…22) | JJ9 | Underpair | Below both distinct ranks |
| AK | QQ5 | Ace high | Board pair only |
| A5 | T55 | Trips | |
| 55 | A25 | Set | |
| AA | 555 | Full house | Board trips count as Hero's hand |
| AK | QQQ | Ace high | |
| KT | 999 | No made hand | |
| 77 | K52 | 2nd pair | One rank (K) above |
| QQ, JJ, TT | K92 | 2nd pair | One rank above |
| A9 | K92 | 2nd pair | Pairs position 2 |
| 88, 77…44 | K93 | 3rd pair | Two ranks above |
| A3 | K93 | 3rd pair | Pairs position 3 |
| 22 | K93 | Underpair | |
| QJ | A72 | No made hand | Ace on the board, not in hand |
| 6h5h | KhQh6s | 3rd pair | (and a flush draw: part 4) |
| JT | TJ3 | Two pair | |
| AT | T5A | Two pair | |
| QJ | Q73 | Top pair | |
| 99 | T82 | 2nd pair | |
| 66 | T82 | 3rd pair | |
| A2 | K92 | 3rd pair | |
| TT | QQ6 | 2nd pair | |
| 44 | QQ6 | Underpair | |
| AA | KK3 | Overpair | |
| A8 | 877 | Top pair | Distinct ranks 8, 7; the 77 is the board's |
| K9 | KK9 | Full house | |
| 98 | 98K | Two pair | |
| KQ | AJT | Straight | |

The user did not review these extra cases; they follow from the rules (assistant's call):
99 on JJ9 → Full house; AQ on QQ5 → Trips; 55 on 55T → Quads; AhQh on QhJh2h → Flush
(not Top pair: the flush wins by priority); A5 on 432 → Straight.

## Where the type is computed — builder's call: in Python, like flop types

A pure module `hand_strength.py`: a `HAND_TYPES` registry (names in priority order) and
`hand_type(hole, board) -> str` over decoded `(rank, suit)` cards, plus a card-id wrapper.
Board length is 3 in part 1; the function should not assume 3 where it costs nothing, since
part 2 reuses it for 4–5 cards.

We compute it ourselves instead of reading PT4's `cash_hand_player_combinations` because the
user's definitions differ from PT4's (paired-board pairs, Ace high). PT4's columns become the
validation oracle (below). `db.run_spot_query` also returns `chps.holecard_1, holecard_2`.
`spotlight.run_spot` labels and filters hands in the same place it handles flop/turn/river
types (`_with_board_types`), **before** labels / distribution / split / details.

## API and page

- `POST /spot` takes `hand_types: list[str] = []`. Deduped, order kept. Unknown name →
  `SpotInputError` → 400 naming it. Empty = Any.
- `hand_types` with a turn or river decision → 400 (fail loud), like `turn_types` with a
  flop decision.
- Response gains `hand_split`: `None` unless the decision is on the flop. Otherwise a list of
  rows in `HAND_TYPES` order, **only types with hands > 0**:
  `{hand_type, hands, pct_total, cells: [{label, hands, pct}]}`. `pct_total` = row / all
  hands in the (filtered) result; cell `pct` = row-relative. **Cells are the distribution's
  rows, in its order, size rows included** (user's call): on a B/X decision `B`, `Bs`,
  `Bm`, `Bl`, `Bo`, `X`, size cells as sub-columns of `B`. On an F/C/R decision the cells are
  `F`, `C`, `R` as in `distribution` (the faced size already has its own facing split table,
  and `vs Bs?` in the Line narrows it); assistant's call. If the table gets too wide, the
  presentation is revisited with real data.
- Interpreted filter: part `Hand: Top pair, Overpair` when set.
- Hand list: a `Hand type` column (next to `Cards`/`Flop` is fine; builder's call), filled
  on flop decisions, empty otherwise. `get_hand_details` is not touched (the NL path).
- Bar: a `Hand` multi-select built with the existing `multiSelect` builder, options from the
  `spot-config` JSON block (checked against `HAND_TYPES` by `test_static_config.py`).
  Disabled when the Line's decision is not on the flop, same mechanism as Turn/River.
- Breakdown table: rendered under the distribution (and under the facing split when there is
  one; the two are shown one under the other, not combined). Columns: `Hand type`,
  `Hands (% total)`, one per action. Clicking a cell selects that type × action in the hand
  list; clicking the row header selects the type. Reuses the split table's label → groups
  click machinery, extended so a pick can also match the hand's type. One pick at a time
  across all tables (a size row and a hand type are not combined); assistant's call.
- Applied on Run only, like every other control.

The user worried the table could get tall; hiding empty rows is the first answer. Revisit
with real data. Typical use (user): narrow by board type first, then look at hand strength.

## Testing

TDD, red then green.

- `hand_strength` (pure): every fixture above (exact type); priority conflicts (flush over
  pair, full house over trips, set over everything below); invariant over a large sample of
  (hole, flop) pairs: exactly one type, and a type from `HAND_TYPES`.
- `spotlight` (mocked DB): filter with OR, AND with flop types; empty keeps all; unknown →
  error; turn/river decision + `hand_types` → error; `hand_split` rows / pcts / zero rows
  dropped; `hand_split` is `None` on a turn decision; filter text part; hand column.
- `api`: list passes through; errors → 400.
- Page config test extended for the new options.

## Validation against PT4 (`db`-marked test)

No PT4 export is needed. For **every** Hero hand that saw the flop, join
`cash_hand_player_combinations` (flop columns) and assert our type is in the set allowed by
PT4's code. Mapping read in the Session 64 spike (`SCHEMA_NOTES.md`):

| PT4 flop category + `id_f_hand_strength` (`val_f_hole_cards_used`) | Our type |
|---|---|
| highcard (any) | Ace high or No made hand (by an Ace in hand) |
| 1pair 0 (used 0) | Ace high or No made hand |
| 1pair 0 (used 2) | Underpair |
| 1pair 1 / 2 / 3 (used 1) | 3rd / 2nd / Top pair |
| 1pair 4 / 5 / 6 (used 2) | 3rd pair / 2nd pair / Overpair |
| 2pair 3 (used 1) | Top pair or 2nd pair |
| 2pair 4 / 5 / 6 (used 2) | Underpair / 2nd pair / Overpair |
| 2pair 7 / 8 / 9 | Two pair |
| threeoak 0 (used 0) | Ace high or No made hand |
| threeoak 1, 3 (used 1) | Trips |
| threeoak 4 / 5 / 6 | Set |
| straight / flush / fullhouse / fouroak / strflush flags | Straight / Flush / Full house / Quads / Straight flush |

Any hand outside its allowed set is a bug in our rules or in the mapping and must be explained
before merge; record the result in `SCHEMA_NOTES.md`. The mapping comes from samples, so a
mismatch may also correct the mapping, but only with the specific hands shown. A mismatch
is a **stop point**: bring the hands to the user before changing rules or mapping. The 9-recipe
oracle must stay green (no `hand_types` = today's behavior).

## Out of scope

Turn/river, subcategories, kickers, draws (parts 2–4); a chart view (the user chose the table;
the SPEC keeps charts in dashboards).
