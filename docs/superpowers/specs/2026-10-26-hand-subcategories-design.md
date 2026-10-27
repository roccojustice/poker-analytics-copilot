# Hand subcategories: Set, Trips, Two pair, Top pair, 2nd pair (M7 #7, part 3b) — Design

*Session 66, 2026-10-26. Brainstormed with the user. Extends parts 1–3a
(`2026-10-21-hand-strength-*-design.md`, `2026-10-24-nut-flush-design.md`); everything there
still holds unless changed here.*

## Problem

The user plays these made hands differently depending on which set, which two pair, and
how good the kicker is, and wants the breakdown to show it. Today each one is a single type.
The `Flush` group pattern (part 3a) worked well ("con el caret está genial"), so the same
pattern is used for five more types.

## What changes

1. **Five types become groups.** In `HAND_TYPES`, each type is replaced in place by its
   leaves, in this order; the old name becomes a `HAND_GROUPS` entry over those leaves
   (like `Flush`). `hand_type` returns leaves only.

   | Group | Leaves, in order |
   |---|---|
   | Set | Top set · Middle set · Bottom set |
   | Trips | Trips Tk · Trips Gk · Trips Nk |
   | Two pair | Top two · Top + other · Bottom two |
   | Top pair | Top pair Tk · Top pair Gk · Top pair Nk |
   | 2nd pair | 2nd pair Tk · 2nd pair Gk · 2nd pair Nk · 2nd pair PP |

   The leaf names are the assistant's proposal, accepted by the user. Which hands fall into
   each group does not change: only the split inside the group is new.
2. **Kicker rule** (user-confirmed, same for Trips, Top pair, 2nd pair): the kicker is Hero's
   hole card that is not part of the pair / trips. Rank the ranks **not on the board** from
   high to low; the kicker's place in that list gives: 1st = `Tk`, 2nd or 3rd = `Gk`, 4th
   or lower = `Nk`. It is relative: on A95, K is the top kicker (K9 → `2nd pair Tk`); on KK5,
   A is `Tk` and Q, J are `Gk`.
3. **Set rule** (user-confirmed): compare Hero's set rank with the board's distinct ranks:
   the highest → `Top set`, the lowest → `Bottom set`, anything else → `Middle set` (on the
   turn / river there can be more than one middle rank).
4. **Two pair rule** (user-confirmed; only hands that are `Two pair` today, i.e. both hole
   cards pair the board and both pairs play): both of Hero's ranks are the two highest
   distinct board ranks → `Top two`; one of them is the highest → `Top + other`; neither →
   `Bottom two`.
5. **2nd pair**: a hole card pairing the board's 2nd rank gets a kicker leaf (rule 2). A
   pocket pair that is `2nd pair` today (between the board's top two ranks, e.g. 88 on A73)
   is `2nd pair PP`, with no kicker (user: "no hay 2nd pair Gk si mi mano es 88 en A73").
   3rd pair, 4th pair, Overpair and Underpair are unchanged.
6. **Kicker on the board (assistant's call).** On the river a hole card can pair the board
   without playing (Hero K5 on KQQ95: top pair, the 5 is on the board). That hand has no
   real kicker: it is `Nk`. Kickers are ranked by rank only; whether the kicker is among the
   best five cards is not checked.
7. **Breakdown, page, filter API.** No new mechanism: they are already driven by
   `HAND_GROUPS` (group row before its first leaf, leaf rows with `parent`, ▸ caret collapsed
   on every run, grouped `Hand` dropdown, `hand:<group>` picks match the leaves,
   `hand_types` takes leaves only, a group name is a 400). The page's `spot-config`
   `hand_groups` gets the five new entries (checked by `tests/test_static_config.py`).

## Examples (test fixtures)

Suits are rainbow unless they matter.

| Hole | Board | Type |
|---|---|---|
| KK | K72 | Top set |
| 77 | K72 | Middle set |
| 22 | K72 | Bottom set |
| 77 | KT72 (turn) | Middle set |
| TT | KT72 (turn) | Middle set |
| AK | KK5 | Trips Tk (A: 1st off the board) |
| KQ | KK5 | Trips Gk (Q: 2nd, the K is on the board) |
| KJ | KK5 | Trips Gk (3rd) |
| KT | KK5 | Trips Nk (4th) |
| KT | KT2 | Top two |
| K2 | KT2 | Top + other |
| T2 | KT2 | Bottom two |
| AK | K72 | Top pair Tk |
| KQ | K72 | Top pair Gk |
| KJ | K72 | Top pair Gk |
| KT | K72 | Top pair Nk |
| AT | KT5 | 2nd pair Tk |
| K9 | A95 | 2nd pair Tk (the A is on the board) |
| QK | AQ5 | 2nd pair Tk |
| Q8 | K85 | 2nd pair Gk (A, **Q**) |
| J8 | K85 | 2nd pair Gk (A, Q, **J**: 3rd) |
| T8 | K85 | 2nd pair Nk |
| 88 | A73 | 2nd pair PP |
| K5 | KQQ95 (river) | Top pair Nk (kicker on the board) |

## Validation against PT4 (`db`-marked, extends `tests/test_hand_strength_db.py`)

Session 66 spike (flop, all Hero flop hands):

| PT4 | Allowed |
|---|---|
| 1pair, our Top pair / 2nd pair (board-card pair), `id_f_kicker_strength` 1 | `… Tk` |
| same, kicker strength 2–3 | `… Gk` |
| same, kicker strength ≥ 4 | `… Nk` |
| threeoak, used 2, strength 6 / 5 / 4 | Top / Middle / Bottom set |
| 2pair, strength 9 / 8 / 7 | Top two / Top + other / Bottom two (*expected, confirm*) |
| 1pair, strength 5, used 2 (pocket pair) | 2nd pair PP |

Our relative kicker matched PT4's `id_f_kicker_strength` on a perfect diagonal for Top pair
(kicker places 0–7 → 1–8, ~5,500 hands) and 2nd pair (~2,900 hands). **Trips does not
match**: PT4's trips kicker strength is ≥ ours but not equal (spread across 1–11). The
builder investigates what PT4 measures there; if it cannot be mapped exactly, Trips is
validated by unit fixtures only and that is recorded in `SCHEMA_NOTES.md`. Turn and river
codes are checked the same way (expect the flop codes to differ, as in part 2); a code that
can't be mapped exactly falls back to the group level for that street, written down.

Exact equality per street on every Hero hand; a mismatch is a stop point. New PT4 facts go
into `docs/SCHEMA_NOTES.md`. Spotlight-level `db` check: leaf rows sum to each group row
(the existing test already loops over `HAND_GROUPS`).

**The user's rules are authoritative; PT4 is the oracle only where it measures the same
thing.** A mismatch means: stop and inspect the mismatched hands. If our code is wrong, fix
it. If PT4 measures something else (e.g. an absolute Trips kicker), keep the user's rule,
map that PT4 code to the whole group's leaves (same approach as part 2's `MIDDLE`), and
record it in `SCHEMA_NOTES.md`. This applies on every street, including flop codes not yet
confirmed: Two pair 9 / 8 / 7, and Top pair / 2nd pair on paired boards (PT4's `2pair`
category, e.g. `("2pair", 3, 1)`, `("2pair", 5, 2)` → `2nd pair PP`), where the kicker
diagonal was not checked by the spike. *(Assistant's call, from the builder check.)*

## Builder notes (from the builder check; assistant's calls)

- The page's `spot-config` also needs the new leaves in its hand-type list, not only in
  `hand_groups`.
- Existing fixtures that now need leaf names fit the rules: Kh9s on JJ9 → `2nd pair Gk`,
  TT on QQ6 → `2nd pair PP`, 5c2h on KK52 → `2nd pair Nk` (kicker on the board), Kc5h on
  22K5 → `Top two`.
- Tests that pass a group name as `hand_types` (e.g. `"Top pair"` in `tests/test_api.py`)
  now get a 400 and switch to leaf names; `test_every_hand_type_occurs` covers the leaves.

## Out of scope

Kicker subcategories for 3rd / 4th pair, Overpair, Underpair; whether the kicker plays;
nut-ness of straights or sets vs. a possible flush; draws (part 4); cosmetic page issues the
user noted for later.
