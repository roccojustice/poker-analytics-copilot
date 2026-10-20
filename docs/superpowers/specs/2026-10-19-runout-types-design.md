# Runout filters: turn and river (M7 #6, part 2) — Design

*Session 63, 2026-10-19. Brainstormed with the user. Follows the flop type filter
(`2026-10-18-flop-type-design.md`) and reuses its shape.*

## Problem

On the turn and river the user studies what the new card did to the board: did it close a
flush, close a straight, pair the board, bring a broadway overcard, or blank out (a brick)?
PT4 cannot filter on any of this. The user needs it to see which hands they bet or checked
on each kind of runout card and compare that against GTO Wizard.

What the card did to **Hero's hand** (made a pair, trips, nothing) is a different filter,
M7 #7 hand strength, and is out of scope here. It waits on its own PT4 schema spike.

## Solution in one paragraph

Two multi-select controls on the bar, **Turn** and **River**, list the runout labels.
Nothing checked = Any. A card can carry several labels at once, and checking several labels
keeps the hands whose card carries **any** of them (OR, like Formations and Flop). Flop, Turn
and River combine with AND. On **Run** the whole result (interpreted filter, distribution,
facing split, hand list) is computed over the remaining hands, and the hand list shows each
hand's turn and river labels. The Turn control only works when the Line's decision is on
the turn or river. The River control only works when the decision is on the river.

## The labels (the user's definitions)

Every label is judged against the **previous board**: the flop for the turn card, the flop
plus turn for the river card. Ranks: 2 low … A high; the A also plays low for straights.

| Label | Streets | Rule |
|---|---|---|
| `FC` (flush closes) | turn, river | After the card, the board holds **3 or more** cards of the card's suit |
| `SC` (straight closes) | turn, river | The card's rank is **new** to the board, and together with two other distinct board ranks it forms a trio whose span (highest − lowest) is **3 or less**. A counts as 14 and as 1 (A-K-Q and A-2-3 both qualify) |
| `BP high` / `BP mid` / `BP low` | turn, river | The card's rank equals a rank already on the board. Over the **distinct** ranks of the previous board: equal to the highest = high, the lowest = low, any other = mid |
| `BW A` / `BW K` / `BW Q` / `BW J` | turn, river | The card is A, K, Q or J **and** strictly higher than every card of the previous board (T does not count) |
| `FDP` (flush draw possible) | turn only | After the card, the board holds **exactly 2** cards of the card's suit |
| `Brick` | turn, river | None of FC, SC, BP *, BW *. FDP does not matter |

User-confirmed rules and examples:
- Labels overlap freely (e.g. a K♥ can be `BW K` + `FDP` + `SC`). Only `Brick` is exclusive,
  and only against FC / SC / BP / BW.
- FC counts a monotone flop + same-suit turn (4 to the suit), and a river that brings a 4th
  card of a suit the turn already completed. Kept simple on purpose; may be refined later.
- SC is the "connected" rule (variant D, chosen by the user over the broad "any new straight
  possible", which marked 36.8% of turns). Span ≤ 3 means several hole-card combos make the
  straight (7-8-9: JT, T6, 65); span 4 is a board gutshot only one combo completes (5-7-9:
  86) and does **not** count. Examples: flop 9-7-2, turn 8 → SC (span 2); turn T → SC
  (T-9-7, span 3); turn 5 → not SC (9-7-5, span 4). On 7-8-9 a turn T is SC (8-9-T), a turn
  2 is not. Flop K-8-3, turn 9 / 7 / 6 → not SC. A card that pairs the board is never SC.
- BP on the river vs a 4-distinct-rank board K-9-6-3: river 9 and river 6 are both `BP mid`.
  On a paired board, e.g. flop 7-7-2: turn 7 = `BP high`, turn 2 = `BP low` (distinct ranks
  7, 2; no mid). *The paired-board case is the assistant's proposal; the user did not object.*
- BW examples from the user: turn K♥ on 9♠7♣3♥, turn Q♠ on J♠8♦3♥. A turn K on a K-high
  flop is `BP high`, not BW. On the river, A on K-9-6-3 is `BW A`; Q on K-9-6-3 is not.
- `Brick` is the user's "carta blanca": doesn't complete draws, doesn't pair, and is not a BW.
  FDP can be a brick.

**Grouping.** `BP` and `BW` are parent options over their sub-labels, like `B` over
`Bs…Bo`: checking the parent checks all its children. The API only deals in leaf labels.

**Share of turns** over all 1,082,900 (flop, turn) pairs, computed this session with a
throwaway script implementing the rules above (sanity reference, not a test):

| FDP | Brick | SC | FC | BW A | BP high | BP low | BP mid | BW K | BW Q | BW J |
|---|---|---|---|---|---|---|---|---|---|---|
| 42.7% | 39.7% | 22.0% | 13.4% | 6.4% | 5.9% | 5.9% | 5.1% | 4.9% | 3.6% | 2.6% |

Page order (builder's call): FC, SC, BP (high, mid, low), BW (A, K, Q, J), FDP, Brick.
The River control omits FDP.

## Where the labels are computed — builder's call: in Python, like flop types

`board_types.py` gains the registries (`TURN_LABELS`, `RIVER_LABELS`, leaf names in page
order) and `runout_labels(previous_cards, card, street) -> set[str]` over decoded
`(rank, suit)` cards, plus a card-id wrapper. `db.run_spot_query` also returns
`chs.card_4, chs.card_5`. `spotlight.run_spot` computes the labels and drops non-matching
hands in the same place it drops flop types, **before** labels / distribution / split /
details. Same reasons as the flop design: one function serves the filter and the hand-list
column, and the rules stay testable without a DB.

A card id outside 1–52 raises, but only for a street that is being labeled: a decision on
the turn never touches `card_5` (the hand may have no river).

## API and page

- `POST /spot` takes `turn_types: list[str] = []` and `river_types: list[str] = []`. Deduped,
  order kept. An unknown label is a `SpotInputError` → 400 naming it. Empty = Any.
- Not applicable → 400 (fail loud): `turn_types` with a flop decision, `river_types` with a
  flop or turn decision. Decision street = `spec.decision.street`.
- `run_spot(..., turn_types=(), river_types=())`.
- Interpreted filter: after `Flop type: …`, parts `Turn type: FC, BP high` and
  `River type: Brick` when set; no part when empty. (`Turn:` / `River:` already open the
  street texts.)
- Hand list: a `Turn type` column after `Turn` and a `River type` column after `River`, each
  the hand's labels joined with ", " in page order. Filled only when the street is labeled
  (decision on that street or later); otherwise empty. `get_hand_details` is not touched.
- Bar: two `<details>` multi-selects after Flop, built with the existing `multiSelect`
  builder, extended for parent/child options. Summary `Turn: Any` / checked labels; a fully
  checked group may read as its parent (`BP`). The control is disabled (and its selection
  ignored) when the current Line's decision street doesn't allow it. The page learns the
  decision street from what it already knows about the Line, or from a cheap parse; builder's
  call. Labels live in the `spot-config` JSON block, checked by `test_static_config.py`
  against the registries.
- Applied on Run only, like every other bar control.

## Testing

TDD, red then green.

- `board_types` (pure):
  - each rule's examples above as fixtures, plus every board in the appendix (exact label
    set, not just "contains");
  - boundary cases: A-low and A-high trios for SC (turn 3 on A-2-9 → SC; turn J on A-K-4 →
    SC), span-4 trios not SC, trips on board as BP, BW vs a paired top card;
  - invariants over all (flop, turn) pairs and a sample of (turn board, river): `Brick` is
    exclusive of FC/SC/BP/BW; at most one BP sub-label and one BW sub-label; every card
    is Brick or carries one of FC/SC/BP/BW; FDP never on the river; BW never on a card that
    pairs the board.
- `spotlight` (mocked DB): selected labels filter with OR, Flop/Turn/River with AND; empty
  keeps all; unknown label → error; not-applicable street → error; filter-text parts; hand
  columns.
- `api`: both lists pass through; unknown / not applicable → 400.
- `db`-marked: on one turn-decision Line, `Brick` and the union of FC/SC/BP/BW partition the
  unfiltered result (hand ids); each hand's `Turn type` contains the label it was filtered by.

## Validation

No PT4 export exists for these categories. The rules are pinned by the user-reviewed
fixtures (appendix) and the invariants; card decoding is already validated.

## Out of scope

- Hand strength / what the card does to Hero's hand (M7 #7).
- Straight-draw-possible, two-tone vs rainbow, trips-on-board as their own labels; add later
  if needed.
- A breakdown table by runout label (filter only, like flop types).

## Appendix — example boards (test fixtures)

From the user: **BW K** flop 9s7c3h → turn Kh; **BW Q** flop Js8d3h → turn Qs.

The rest were generated by the assistant from the rules (random boards, seed fixed) and are
**pending the user's review**. Format: previous board → new card [full label set]. Each
fixture asserts the exact set.

**Turn**

| Label | Examples |
|---|---|
| FC | JdJcQc → 5c [FC] · Kh9c6h → Jh [FC] · 3cAcTs → Jc [FC] |
| SC | 9c6hKd → 8c [SC + FDP] · 6h4cKs → 5s [SC + FDP] · 9c8dTs → 6d [SC + FDP] |
| BP high | 3s9s9d → 9h [BP high] · 4cTh4d → Td [BP high + FDP] · 6d9cTc → Th [BP high] |
| BP mid | KcTd6c → Ts [BP mid] · 8sQs6c → 8d [BP mid] · 4h6c2s → 4s [BP mid + FDP] |
| BP low | Ts2sQc → 2d [BP low] · KhAc5d → 5h [BP low + FDP] · KsQd9d → 9s [BP low + FDP] |
| BW A | 5h9c7d → Ac [BW A + FDP] · TcTdQc → Ah [BW A] · 2h8sKd → Ac [BW A] |
| BW K | 5s2d8h → Kd [BW K + FDP] · 4d8h2s → Kd [BW K + FDP] · 5h3h9h → Kd [BW K] |
| BW Q | 5s8h3c → Qd [BW Q] · 2sTs4d → Qd [BW Q + FDP] · 5s8s8c → Qh [BW Q] |
| BW J | 6c4h7c → Js [BW J] · 5h4d6h → Js [BW J] · 2d2s2c → Jc [BW J + FDP] |
| FDP | 7sJs9h → 4h [FDP + Brick] · Kh9s5s → 4h [FDP + Brick] · 2c2h2s → Th [FDP + Brick] |
| Brick | 5c4d8h → Td [FDP + Brick] · 3c6sQc → 2s [FDP + Brick] · 6c5hQd → 2h [FDP + Brick] |
| Overlaps | 7sJh9h → Qc [SC + BW Q] · Kc7cTh → Jc [FC + SC] · 8h3s2h → Jh [FC + BW J] · 8c9dTd → Qd [FC + SC + BW Q] · Qs7hJh → Kd [SC + BW K] |

**River** (flop turn → river)

| Label | Examples |
|---|---|
| FC | AcJhQd 2h → 7h [FC] · 9d9cKc Ad → 6c [FC] · Jd5h4c 7d → 9d [FC] |
| SC | 6d6sAc Kd → Js [SC] · Qh3h5c 8c → 4d [SC] · 3s9d8s 7c → 6c [SC] |
| BP high | Js8hTd Qs → Qh [BP high] · 8d2s2c 3c → 8h [BP high] · 2cQh5d 3c → Qd [BP high] |
| BP mid | 6h9d7s 8s → 8h [BP mid] · 4c7d3h Qh → 7s [BP mid] · 7d9hAd Td → Ts [BP mid] |
| BP low | 2s8d6s 3h → 2c [BP low] · 6c2sKd 2h → 2c [BP low] · JhTd2h 8d → 2s [BP low] |
| BW A | Qc3sTs 8s → Ac [BW A] · 7s2c2h Js → Ah [BW A] · 6d6cTh 2d → Ac [BW A] |
| BW K | 4hQc6d 5s → Kd [BW K] · 7c2s8h Js → Kd [BW K] · 9dJc2c 9h → Ks [BW K] |
| BW Q | Ts8dTc 8h → Qs [BW Q] · 4c2s5d Th → Qd [BW Q] · 5d2s4s 8s → Qc [BW Q] |
| BW J | 3s2s4c 3c → Jh [BW J] · 7c9d5s 4h → Jc [BW J] · 6c2d8s 8d → Js [BW J] |
| Brick | 2s5s3c Jh → 7d [Brick] · AsAc9d Jd → 4s [Brick] · 3dAh5s 4d → Kh [Brick] |
