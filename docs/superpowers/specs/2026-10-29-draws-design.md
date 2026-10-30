# Draws (M7 #7, part 4) — Design

*Session 67, 2026-10-29. Brainstormed with the user. Builds on the hand-strength parts
(`2026-10-21-hand-strength-*-design.md`, `2026-10-24-nut-flush-design.md`,
`2026-10-26-hand-subcategories-design.md`); everything there still holds.*

## Problem

In GTO Wizard each draw type has its own bet / check / raise frequencies. The user wants to
see his own frequencies per draw type in any spot, to check he executes them. That only works
if the tool's draw categories are **GTO Wizard's, with GTO Wizard's rules**: otherwise the
comparison is apples to oranges.

## The dimension

A second hand dimension, **independent of the made-hand type** (`hand_strength`): every hand
gets exactly one hand type *and* exactly one draw type (A♠K♦ on J♥8♥3♣ = Ace high + No draw;
8♣7♣ there = Second pair + BDFD 2 cards). Inside the dimension the types are mutually
exclusive (GTO Wizard's help: "each hand only belongs to one category"); across dimensions
filters combine with AND, as GTO Wizard's Hands and Draws panels do.

## Draw types (GTO Wizard's names and order = priority; the first that applies wins)

| # | Type | Rule |
|---|---|---|
| 1 | Combo draw | a flush draw (nut or not) **and** a straight draw (OESD or gutshot) |
| 2 | Flush draw nuts | a flush draw whose highest hole card of the suit is the highest rank of that suit off the board (same rule as `Nut flush`) |
| 3 | Flush draw | any other flush draw |
| 4 | OESD | straight draw with 8 outs (2 out-ranks): open-ended **or double gutshot** |
| 5 | Gutshot | straight draw with 4 outs (1 out-rank) |
| 6 | BDFD 2 cards | flop only: both hole cards of one suit + 1 board card of it |
| 7 | BDFD 1 card | flop only: 1 hole card of a suit + 2 board cards of it |
| 8 | No draw | everything else; **every hand on the river** |

Definitions:

- **Flush draw** (flop / turn): some suit has exactly 4 cards among hole + board and at least
  one of them is a hole card. One hole card is enough (A♥5♣ on K♥8♥4♥).
- **Straight draw** (flop / turn): Hero has no straight yet; an *out-rank* is a rank whose
  card would give Hero a straight that uses at least one of his hole cards (each rank = 4
  outs). 2 out-ranks (8 outs) = OESD, 1 (4 outs) = Gutshot; with 2 hole cards and no straight
  yet there are never more than 2. One hole card is enough (66 on 987). A made straight blocks straight
  draws (J♦T♦ on 9♠8♦7♣ is BDFD 2 cards, not Gutshot to the higher straight). Ace counts
  low too (wheel).
- **Backdoor flush draw**: flop only, only when there is no flush draw.

## Confirmed against GTO Wizard by the user (unit fixtures, `tests/test_draws.py`)

| # | Board | Hole | Draw type |
|---|---|---|---|
| 1 | J♥8♥3♣ | A♥5♥ | Flush draw nuts |
| 2 | J♥8♥3♣ | K♥5♥ | Flush draw |
| 3 | J♥8♥3♣ | T♥9♥ | Combo draw (FD + OESD) |
| 4 | J♥8♥3♣ | Q♥T♥ | Combo draw (FD + gutshot) |
| 5 | J♥8♥3♣ | T♠9♠ | OESD |
| 6 | J♥8♥3♣ | T♣9♣ | OESD (beats BDFD) |
| 7 | J♥8♥3♣ | A♣K♣ | BDFD 2 cards |
| 8 | J♥8♥3♣ | A♥K♣ | BDFD 1 card |
| 9 | J♥8♥3♣ | A♠K♦ | No draw |
| 10 | J♥8♥3♣ | 8♣7♣ | BDFD 2 cards (a pair doesn't block) |
| 11 | 9♠8♦7♣ | T♥9♥ | OESD (pair + OESD is not Combo) |
| 12 | 9♠8♦7♣ | 6♥6♦ | OESD (one hole card) |
| 13 | 9♠8♦7♣ | J♦T♦ | BDFD 2 cards (made straight: no straight draw) |
| 14 | 9♥7♦5♣ | J♠8♦ | OESD (double gutshot) |
| 15 | K♥8♥4♥ | A♥5♣ | Flush draw nuts (one card) |
| 16 | K♥8♥4♥ | Q♥J♣ | Flush draw (one card) |
| 17 | K♥8♥4♥ | A♣A♦ | No draw |
| 18 | A♥8♥3♣ | K♥5♥ | Flush draw nuts (the A is on the board) |
| 19 | J♥8♥3♣2♠ | A♥K♥ | Flush draw nuts (turn) |
| 20 | J♥8♥3♣2♠ | A♣K♣ | No draw (no backdoors on the turn) |

Plus: any river board → No draw (user's GTO Wizard screenshot: river = 100% No draw).

## Where it goes

Mirrors the hand-type dimension; the builder follows the existing patterns.

- **`draws.py`**, pure, no DB: `DRAW_TYPES` (the 8 names above, in order) and
  `classify_draw(hole, board)` for 3–5 board cards / `draw_type(holecard_1, holecard_2,
  *board_ids)`. Reuse `hand_strength` helpers (`_value`, `_straight_high`, `_best`, the
  nut-flush rule) rather than duplicating them. No groups.
- **`spotlight.py`**: `draw_type` column on the decision street's board (`BOARD_SIZE`), right
  next to `hand_type`; `draw_types` filter (validated by `_checked` against `DRAW_TYPES`,
  unknown → `SpotInputError`, applied before labels / distribution / splits / details);
  `describe` adds `Draw: …`; `draw_split` = one row per draw type with hands, same shape as a
  `hand_split` leaf row (`draw_type`, `hands`, `pct_total`, `cells`). On the river the filter
  is allowed (everything is No draw), it is not an error.
- **`api.py` `POST /spot`**: accepts `draw_types` like `hand_types`.
- **`static/index.html`**: a `Draw` checkbox dropdown (same `multiSelect` builder, flat, not
  grouped) and a draw × action table under the hand table (same rendering as the hand
  table, rows with hands only). Picks accumulate: one action pick AND one hand pick AND one
  draw pick (`draw:<type>` / `draw:<type>|<label>`); each table is recounted over the hands
  passing the other two tables' picks; a draw-table cell sets the draw and the action pick.
  `spot-config` gets `draw_types`, checked against `draws.DRAW_TYPES` by
  `tests/test_static_config.py`.

## Validation against PT4 (`db`-marked, `tests/test_draws_db.py`)

**The GTO Wizard rules above are authoritative; PT4 is the oracle only where it measures the
same thing.** `cash_hand_player_combinations` has per-street draw flags for flop and turn
(`flg_<s>_flush_draw`, `_straight_draw`, `_gutshot_draw`, `_bflush_draw`, …;
`SCHEMA_NOTES.md`, "Hand strength per street"; `.env` now points at
`PT4_2026_10_29_075726`, the user's duplicate of the old DB, so existing `db` test counts may
shift if it holds new hands). First step: read a sample of each draw column to learn what it
means (whether it needs a hole card, whether a double gutshot
is `straight_draw`, whether a made flush / straight clears it, whether there is a nut flag).
Then, on every Hero flop and turn hand, compare by exact set membership:

Draw columns present (listed Session 67): `flg_<s>_flush_draw`, `flg_<s>_straight_draw`,
`flg_<s>_2gutshot_draw`, `flg_<s>_gutshot_draw`, `flg_<s>_wrap_draw`, `flg_<s>_low_draw`,
`flg_f_bflush_draw`, `flg_f_bstraight_draw`, `id_<s>_flush_draw_strength`,
`val_<s>_straight_draw_nut_outs` / `_nonnut_outs`, `val_<s>_low_draw_strength`
(`<s>` = `f`, `t`). Wrap and low draws are Omaha / hi-lo; expect them always false.

| Ours | PT4 (expected) |
|---|---|
| has a flush draw (Combo with FD, Flush draw nuts, Flush draw) | `flg_<s>_flush_draw` |
| nut flush draw | a value of `id_<s>_flush_draw_strength` (decode it, as for the flush) |
| 2 out-ranks | `flg_<s>_straight_draw` ∪ `flg_<s>_2gutshot_draw` |
| 1 out-rank | `flg_<s>_gutshot_draw` |
| BDFD 2 cards ∪ 1 card (flop) | `flg_f_bflush_draw` (no 1/2-card split in PT4: that split rests on unit fixtures) |

Compare the underlying draws, not just the priority winner (a Combo hand must show both
flags). A mismatch is a stop point: inspect the hands. If our code is wrong, fix it. If PT4
defines the draw differently, keep the GTO Wizard rule, write the difference in
`SCHEMA_NOTES.md`, and restrict the PT4 check to the hands where the definitions agree
(sabotage-check the comparison as in earlier parts). Spotlight-level `db` check: the
`draw_split` rows sum to the result's hand count.

## Builder notes (from the builder check; assistant's calls, not confirmed in GTO Wizard)

- An out-rank counts only if Hero's best five with that card beats the board's best five
  with it (on a 9-8-7-6 turn the T or 5 straight is the board's, not Hero's draw); same idea
  as the "kicker plays" check in `hand_strength._kicker`.
- A made flush blocks flush draws but not straight draws (made flush + OESD → OESD).
- A nut flush draw + a straight draw is Combo draw (priority order; not tested in GTO Wizard).

## Out of scope

Backdoor straight draws, overcards, nut-ness of straight draws, sub-buckets of non-nut
flush draws (GTO Wizard's blog mentions broadway / mid / low; not in the user's panel),
draw groups / carets, and cosmetic page issues.
