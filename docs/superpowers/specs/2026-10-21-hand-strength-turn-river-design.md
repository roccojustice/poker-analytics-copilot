# Hand strength on turn and river (M7 #7, part 2) — Design

*Session 64, 2026-10-21. Brainstormed with the user. Extends part 1
(`2026-10-21-hand-strength-flop-design.md`); everything there still holds unless changed here.*

## Problem

Part 1 labels Hero's made hand only on flop decisions. The user's turn and river lines
(`- B-?`, `vs B-X-?`, …) need the same filter and breakdown, labelled on the **decision
street's board** (4 cards on the turn, 5 on the river).

## What changes

1. **Every decision street.** `hand_type` is computed on the decision street's board: flop
   cards for a flop decision, flop + turn for a turn decision, all five for a river decision.
   The `Hand` control, the breakdown table (`hand_split`) and the `Hand type` column work on
   every Line. The "needs a decision on the flop" error goes away; `hand_split` is never
   `None` (an empty list when there are no hands).
2. **`4th pair`**, a new type between `3rd pair` and `Underpair` (`HAND_TYPES` order). Pairing
   the 4th distinct board rank **or lower** is `4th pair` (no 5th pair, user's words); a pocket
   pair with three or more distinct board ranks above it and at least one below is `4th pair`.
3. **Hero's hand counts only when his hole cards play** (user's rule, generalised from his
   examples). Concretely, in priority order:
   - **Board-made hands (river).** If the five board cards alone make a straight or better
     and Hero's best five do not **beat** them, the hand is `No made hand` (even with an Ace,
     a pair in hand, or a suited card that doesn't play).
   - **Board quads** (four of a kind on the board, turn or river): Hero only adds a kicker →
     `Ace high` if he holds an A, else `No made hand`. Quads count only when a hole card is one
     of the four. *(Assistant's call, consistent with "AK on QQQ = Ace high" and PT4's
     `fouroak used=0`; the user had not decided this case.)*
   - **Made hands** (straight flush, full house, flush, straight) otherwise as in part 1, from
     Hero's best five of all cards.
   - **Pairs play only if they are among the two highest pairs.** Let *P* = the board's pair
     ranks plus Hero's pair ranks (a hole card matching a single board rank, or a pocket pair
     not on the board). A Hero pair plays only if it is one of the two highest ranks in *P*.
     - Two pair: both of Hero's pairs play. If only Hero's higher pair plays, the hand is that
       pair (by position); if none plays, no pair.
     - A pocket pair or single pair that doesn't play → `Ace high` / `No made hand`.
   - Set and Trips are unchanged (they always play when no board-made hand beats them).
   - Positions are counted over the decision board's distinct ranks, high to low.

On a flop this reduces exactly to part 1 (a flop has at most one board pair), so the flop
behaviour does not change.

## Examples (test fixtures; user-confirmed unless marked)

| Hole | Board | Type |
|---|---|---|
| 52 | KK52 | 2nd pair (the 2 does not play) |
| 52 | KK55 | Full house |
| 33 | KK55 | No made hand |
| AQ | KK55 | Ace high |
| 77 | KK55 | 2nd pair |
| K5 | 22K5 | Two pair |
| 66 | KK559 | 3rd pair |
| T2 | 56789 (river) | Straight |
| 4x | 56789 | No made hand |
| AA, 99 | 56789 | No made hand |
| any spade, e.g. 3s4d | KsTs7s5s2s | Flush |
| 2s + non-spade | AsKsQsJs9s | No made hand |
| A2 | K952 (turn) | 4th pair |
| 33 | K952 | 4th pair |
| 22 | K953 | Underpair |
| A3 | K9532 | 4th pair |
| A2 | K9532 | 4th pair (5th rank, capped) |
| 44 | K9532 | 4th pair |
| A + x | KKKK (turn) / KKKK2 | Ace high *(assistant's call)* |
| A3 | KK553 | Ace high: the 3 pair doesn't play, the A plays as kicker *(assistant's call)* |
| Ax | KKKKA | No made hand: doesn't beat the board, the board-made rule fires first *(assistant's call)* |
| 33 / 5x | KKK55 | No made hand; 66 / AA → Full house; K → Quads *(assistant's call)* |

"Beat" is a full five-card comparison, kickers included (that is why the 3s plays on
KsTs7s5s2s). Rules apply strictly in the order listed; the builder check walked double-paired,
board-trips, board-quads and board-straight/flush boards and found exactly one type each.

## Validation against PT4 (`db`-marked, extends `tests/test_hand_strength_db.py`)

Same method as part 1, now per street, over every Hero hand that saw that street
(31,229 turn, 20,280 river), with `id_<s>_hand_strength` / `val_<s>_hole_cards_used` and the
`flg_<s>_*` category flags. PT4 groups positions differently (its "middle pair" covers 2nd to
4th), so the allowed sets are wider than on the flop; the unit fixtures pin exact positions.
Mapping read from the Session 64 turn/river spike:

| PT4 category (strength, used) | Allowed types |
|---|---|
| straight / flush / fullhouse / fouroak / strflush, used 0 | Ace high, No made hand |
| same, used ≥ 1 | that type |
| highcard (any) | Ace high, No made hand |
| 1pair (0, 0) · 2pair (0, 0) · 2pair (5, 0) · threeoak (0, 0) | Ace high, No made hand |
| 1pair (0, 2) · 2pair (4, 2) | Underpair |
| 1pair (3, 1) | Top pair |
| 1pair (1 / 2, 1) · 1pair (4 / 5, 2) · 2pair (1 / 2, 1) · 2pair (5, 2) | 2nd, 3rd or 4th pair |
| 2pair (3, 1) | Top, 2nd or 3rd pair |
| 1pair (6, 2) · 2pair (6, 2) | Overpair |
| 2pair (7 / 8 / 9) | Two pair |
| threeoak (1 / 2 / 3, 1) | Trips |
| threeoak (4 / 5 / 6, 2) | Set |

The flop keeps its part-1 mapping. A hand outside its allowed set is a **stop point**, as in
part 1. Spotlight-level `db` tests (partition, column = filter, all = any, breakdown sums) are
repeated on one turn Line and one river Line.

## Out of scope

Subcategories (part 3), draws (part 4), kickers.
