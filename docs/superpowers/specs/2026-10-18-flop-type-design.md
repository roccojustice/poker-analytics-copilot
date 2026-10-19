# Flop type filter (M7 #6, part 1) — Design

*Session 62, 2026-10-18. Brainstormed and approved with the user. First of the board filters;
runout filters (turn/river) are designed later, separately.*

## Problem

Frequencies and sizings change with flop texture, so a Line's distribution over every flop
hides what the user studies. In M6 run 1 the user fell back to PT4 to look at one kind of
flop at a time. BLL, Low and 2BWL are ~67% of all flops, so those are the ones worth
studying alone.

## Solution in one paragraph

A multi-select **Flop** control on the bar, like Formations, lists the user's 8 flop types.
Nothing checked = Any. On **Run**, the whole result — interpreted filter, distribution,
facing split and hand list — is computed over the hands whose flop is one of the checked
types. The hand list also shows each hand's flop type.

## The 8 flop types (the user's taxonomy)

Broadway = A K Q J T. "Plain" = not paired and not monotone. Evaluated in this order; every
one of the 22,100 three-card flops lands in exactly one type (checked this session).

| Type | Rule | % of flops |
|---|---|---|
| `Monotone` | all 3 cards the same suit, any ranks | 5.2% |
| `Low paired` | paired (pair **or trips**) with the paired rank 2–8; third card any | 9.2% |
| `High paired` | paired (pair or trips) with the paired rank 9–A; third card any | 7.9% |
| `3BW` | plain, 3 broadway cards | 2.7% |
| `2BWL` | plain, exactly 2 broadway cards (third card 2–9) | 21.7% |
| `A high` | plain, one A, the other two 2–9 | 7.6% |
| `BLL` | plain, exactly one of K/Q/J, the other two 2–9 | 22.8% |
| `Low` | plain, all three 2–T (so a T-high flop with two low cards is `Low`) | 22.8% |

User-confirmed rules: trips count as paired; T is broadway for 3BW / 2BWL but a lone T is
`Low`; Monotone wins over every rank rule. The user's own examples for each type (from this
session's conversation) become test fixtures; the first 2BWL example list was wrong (only one
broadway each) and is not a fixture.

The display names above are the canonical spellings, used in the API, the page and the
filter text. Page order (the user's order when defining them): 2BWL, BLL, Low, Low paired,
High paired, A high, Monotone, 3BW.

## Where the type is computed — *builder's call recorded here: in Python, not SQL*

A new pure module `board_types.py` holds the registry (names in page order) and
`flop_type(card_1, card_2, card_3) -> str` over PT4 card ids (decoded with
`poker_cards.decode_card_id`). `db.run_spot_query` also returns `chs.card_1..3`;
`spotlight.run_spot` drops the hands whose type isn't selected **before** labels,
distribution, split and hand details are computed, so everything downstream is filtered with
no other change. Why Python: one function for both the filter and the hand-list column (they
cannot disagree), the 8 rules stay readable and testable without a DB, and Spotlight's row
counts (thousands) make the extra columns cheap. The SQL `WHERE` is unchanged.

Every Spotlight hand saw a heads-up flop, so the three flop cards always exist. A card id
outside 1–52 raises (it would mean a broken join, not a user error).

## API and page

- `POST /spot` takes `flop_types: list[str] = []`. Deduped, order kept. An unknown name is a
  `SpotInputError` → 400 with the name in the message. Empty = Any.
- `run_spot(..., flop_types=())`.
- Interpreted filter: after formations and dates, a part `Flop: BLL, Low` when any type is
  selected; no part when none (like dates).
- Hand list: a `Flop type` column right after `Flop`. Computed in `run_spot` from the cards
  `run_spot_query` already returns (same `flop_type` the filter uses) and merged into the hands
  with `measured_action`; the raw card columns are not sent. `get_hand_details` is **not**
  touched: the frozen NL path also calls it, for hands that may have no flop (card id 0).
- Bar: a `<details>` multi-select after Formations, summary `Flop: Any` / the checked names
  joined with ", ". The list lives in the `spot-config` JSON block; `test_static_config.py`
  checks it equals the registry, in order.
- Applied on Run only, like every other bar control.

## Testing

TDD, red then green.

- `board_types` (pure): every fixture flop from the user's examples gets its type; over all
  22,100 flops each type's count is exactly 2,044 / 1,752 / 600 / 4,800 / 1,680 / 5,040 /
  5,040 / 1,144 (Low paired / High paired / 3BW / 2BWL / A high / BLL / Low / Monotone);
  boundary cases: `TsTd2c` High paired, `8s8d2c` Low paired, `Ts9d8c` Low, `AsTd3c` 2BWL,
  `KsKdKc` High paired, `AsKsQs` Monotone.
- `spotlight` (mocked DB): only selected types reach distribution / split / hands; none
  selected keeps everything; unknown type raises; dedupe; filter-text part.
- `api`: `flop_types` passes through; unknown → 400.
- `db`-marked: for one Line, the 8 single-type results are disjoint and their union is the
  unfiltered result (hand ids and distribution counts); each hand's `Flop type` equals the
  type it was filtered by.

## Validation

No PT4 export: PT4 has no such categories. The rules are pinned by the user's fixtures and
the exact 22,100-flop counts; card decoding is already validated (`poker_cards`). Sanity
check, not a test: on a Line with many hands, each type's share should sit near its % above
(card removal from Hero's hole cards shifts broadway-heavy types somewhat).

## Out of scope

- Turn / river runout filters (flush completes, turn pairs, …): next design.
- A breakdown/table by flop type (the user wants a filter, not a split).
- Two-tone vs rainbow as its own filter.

## Appendix — the user's example flops (test fixtures)

- **2BWL:** AsJd2d AsJd7s AsJs9d AsKd3c AsKd8d AsKs8d AsQd5c AsQs9c AsTd3c JsTd3d JsTd6d
  JsTd6s JsTd7s KsJd7c KsJd7s KsJd9s KsQd3s KsQd5c KsQs9d KsTd2c KsTd2s KsTs6d QsJd4c QsJd6s
  QsJs8d QsTd3d QsTd5s QsTs5d
- **BLL:** Js3d2c Js5d4s Js6d3c Js6d5c Js7d6c Js8d4d Js9d3s Js9d4s Js9d5c Ks4d2s Ks4d3c
  Ks5d4d Ks6d5c Ks6s2d Ks7d3c Ks8d5c Ks8d7c Ks9d3c Ks9d4c Qs4d2c Qs6d5c Qs6s2d Qs7d4s Qs7d5s
  Qs8d3c Qs8d7c Qs8d7s Qs9d6d Qs9d8d
- **Low:** Ts9d5d Ts9d4c Ts8d6c Ts8d4d Ts8d2s Ts8d2c Ts7d4s Ts6d4c Ts5s3d 9s8d6d 9s8d3s
  9s8d2c 9s7d5d 9s6d2c 9s5d2c 9s3d2s 8s7s3d 8s5s4c 8s4d3s 7s6s2d 7s6d4c 7s6d2s 7s4d3c 7s3s2d
  6s5s4d 6s4s3d 5s4d2d 5s3s2d
- **Low paired:** As4d4c Ks6s6d Ks8d8c Js2s2d Ts6s6d 9s4s4d 8s8d6c 8s7d7c 8s5s5d 5s5d5c
  5s3d3c 4s2s2d
- **High paired:** AsAd6d AsQsQd AsAd3d KsKdKc KsKdTc QsQd2c QsJdJc JsJd4c TsTd9d TsTd7c
  9s9d5c 9s9d7d
- **A high:** As9s4d As9d7c As9d7s As8s5d As8d6s As7d5c As5d2c As4s2d As7d2c As3d2s As6d3c
- **Monotone:** As5s3s KsJs5s Qs3s2s JsTs9s Ts7s4s 8s6s2s
- **3BW:** AsKdTc AsQsJd AsQdTs (plus KsQdJc, QhJhTd, confirmed in conversation)
