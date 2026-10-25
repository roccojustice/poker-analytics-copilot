# Nut flush vs other flush (M7 #7, part 3a) — Design

*Session 65, 2026-10-24. Brainstormed with the user. Extends parts 1–2
(`2026-10-21-hand-strength-flop-design.md`, `…-turn-river-design.md`); everything there still
holds unless changed here.*

## Problem

The user believes nut flushes should be played differently from other flushes and wants the
data to confirm or refute it. Today every made flush is one `Flush` type. Only two categories
are wanted (user's words: "nut flush y la otra solo flush"); no 2nd/3rd-nut levels.

## What changes

1. **Two types replace `Flush`**: `Nut flush` and `Other flush`, in that order, in `Flush`'s
   place in `HAND_TYPES` (after `Full house`, before `Straight`). `hand_type` returns one of
   them wherever it returned `Flush`; nothing else in the classifier changes (straight flush,
   "hole cards must play", board-made-hand rule, priority order).
2. **Nut rule** (user-confirmed): take the flush suit; Hero's **highest hole card of that suit**
   is the nut if no rank of that suit above it is missing from the board, i.e. it is the
   highest rank of the suit not on the board. With A♥ on the board, K♥ is the nut; with A♥ K♥
   on the board, Q♥ is. Board pairing (full house possible) and straight-flush possibilities
   are ignored.
3. **Grouping.** `Flush` stays as a **group name** over the two leaves (a small explicit
   mapping next to `HAND_TYPES`). It is not a type `hand_type` returns.
4. **Breakdown table (`hand_split`).** When the result has any flush, a `Flush` row (total
   hands, `pct_total`, cells over both leaves) sits where `Flush` sits today, followed by one
   row per leaf that has hands, each marked with `parent: "Flush"` (same convention as the `B`
   → `Bs…Bo` distribution rows). Leaf rows have their own cells, so nut vs other compares
   directly. Leaf `pct_total` is over all hands, like every other row.
5. **Page — table** (user-chosen): the `Flush` row has a ▸ caret before its name. Clicking
   the caret expands / collapses the indented leaf rows; it does not pick. Collapsed by default
   and again on every new run. Clicking the `Flush` name picks all flushes (both leaves);
   clicking a leaf name or cell picks that leaf (existing `hand:<type>` / `hand:<type>|<label>`
   pick format).
6. **Page — `Hand` dropdown**: `Flush` is a parent checkbox over `Nut flush` / `Other flush`,
   behaving like `BP` / `BW` in Turn/River (parent toggles both, indeterminate when one is
   checked, summary shows `Flush` when both are checked). The current grouping is by first
   word, which would wrongly nest `Straight flush` under `Straight`, so hand types need an
   explicit group; how is left to the builder.
7. **`Hand type` column** in the hand list shows the leaf (`Nut flush` / `Other flush`).
8. **Filter API**: `hand_types` takes the leaves; `Flush` is not accepted (unknown hand type,
   400). The page always sends leaves. *(Assistant's call: one name per type keeps the
   validation and interpreted-filter text unchanged.)*

## Examples (test fixtures)

| Hole | Board | Type |
|---|---|---|
| AhTh | Kh9h4h | Nut flush |
| KhTh | Ah9h4h | Nut flush (A on board) |
| QhJh | AhKh7h | Nut flush (A, K on board) |
| QhTh | Ah9h4h | Other flush (K missing) |
| KhQh | 9h7h4h | Other flush (A missing) |
| Ah2c | Kh9h4h3h (turn) | Nut flush (one suited card) |
| Kh2c | Qh9h4h2h (turn) | Other flush |
| As + x | KsTs7s5s2s (river) | Nut flush (beats the board flush) |
| 3s + x | KsTs7s5s2s | Other flush |
| 2s + x | AsKsQsJs9s | No made hand (unchanged: board plays) |
| 9h8h | Th7h6h | Straight flush (unchanged) |

## Validation against PT4 (`db`-marked, extends `tests/test_hand_strength_db.py`)

Session 65 spike: within PT4's flush category, `id_<s>_hand_strength` = 10 − (ranks of the
suit above Hero's highest suited hole card that are not on the board), a perfect diagonal on
every street (flop 163, turn 667, river 1,107 Hero flush hands). So:

| PT4 | Allowed |
|---|---|
| flush, used ≥ 1, strength 10 | Nut flush |
| flush, used ≥ 1, strength 2–9 | Other flush |
| flush, used 0 | Ace high, No made hand (unchanged) |

Exact equality, every Hero hand per street; a mismatch is a stop point. Add this fact to
`docs/SCHEMA_NOTES.md` (PT4's flush strength code). Spotlight-level `db` breakdown checks:
leaf rows sum to the `Flush` row.

Expect small samples: about 56 nut flushes on the flop, 162 on the turn, 270 on the river
across **all** of Hero's hands, so a single spot will often have a handful.

## Builder notes (from the builder check; assistant's calls)

- The group mapping (`Flush` → leaves) also goes into the page's `spot-config` block, checked by
  `tests/test_static_config.py`. The page uses it for the dropdown and for `matchesPick`
  (`hand:Flush` / `hand:Flush|<label>` match both leaves). The dropdown sends leaves only.
- `tests/test_hand_strength_db.py`: the flush mapping becomes strength-based; any "rows sum to
  the result" check must skip rows with a `parent`.
- The two existing `Flush` fixtures in `tests/test_hand_strength.py` become `Other flush`
  under the nut rule.

## Out of scope

Subcategories of Set, Two pair or other types (later, one by one with the user); nut-ness of
straights; draws (part 4); remembering the expanded state; cosmetic page issues the user
noted for later.
