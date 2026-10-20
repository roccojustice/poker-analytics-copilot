# Runout Filters: Turn and River (M7 #6, part 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn and River multi-selects filter a Spotlight result (distribution, facing split, hands) by what the turn / river card did to the board, and the hand list shows each hand's turn and river labels.

**Architecture:** `board_types.py` gains the runout label rules (pure). `db.run_spot_query` also returns `chs.card_4, chs.card_5`; `spotlight.run_spot` labels the turn when the decision is on the turn or river and the river when it is on the river, filters (OR within a street, AND across Flop / Turn / River) before labels / distribution / split / details, and merges `turn_type` / `river_type` into the hands. `api.py` and the page pass `turn_types` / `river_types` through.

**Tech Stack:** Python 3, FastAPI, pandas, SQLAlchemy/psycopg2 over PT4 Postgres, pytest, vanilla JS.

**Spec:** `docs/superpowers/specs/2026-10-19-runout-types-design.md`

## Global Constraints

- Leaf labels, page order: `FC`, `SC`, `BP high`, `BP mid`, `BP low`, `BW A`, `BW K`, `BW Q`, `BW J`, `FDP`, `Brick`. `board_types.TURN_LABELS` is that tuple; `RIVER_LABELS` is the same without `FDP`.
- Rules, against the previous board (flop for the turn; flop + turn for the river); ranks 2…A = 2…14:
  - `FC`: board after the card holds ≥ 3 cards of the card's suit.
  - `SC`: card's rank is not already on the board, and with two other **distinct** board ranks it forms a trio of distinct values with max − min ≤ 3. A is 14 and 1 (try both).
  - `BP high/mid/low`: card's rank is on the board; over the previous board's distinct ranks it equals the highest / the lowest / any other.
  - `BW <r>`: rank in A K Q J and strictly greater than every previous board rank.
  - `FDP` (turn only): board after the card holds exactly 2 of the card's suit.
  - `Brick`: none of FC, SC, BP *, BW * (FDP ignored).
- Labels per card are returned in page order and joined with `", "` for the hand columns (`"SC, BW Q"`).
- Turn filter allowed only when the decision street is turn or river; river filter only when it is river. Otherwise `SpotInputError` (→ 400). Unknown label → `SpotInputError` naming it. Dedupe, keep order. Empty = Any. All checks run before `run_spot_query`.
- Filter-text parts, after `Flop type: …`: `Turn type: FC, BP high`, `River type: Brick`; nothing when empty.
- `turn_type` is `None` on hands whose decision is on the flop; `river_type` is `None` unless the decision is on the river. An unlabeled street's card is never decoded (`card_5` may be 0).
- `get_hand_details` is not modified.
- Inline comments: one line max. Strict TDD: watch each test fail for the expected reason.
- Branch `m7-runout-types`. Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Run tests with `venv/Scripts/python -m pytest ...` (Bash); `-m db` runs the Postgres tests.

## Review Focus

1. **A turn-decision Line whose hands have `card_5 = 0`** must not raise and must leave `river_type` `None`. Pinned in Task 2.
2. **River filter on a turn-decision Line** (`- B-?` + `river_types=["Brick"]`) is a 400 raised before any DB call, not an empty result. Pinned in Tasks 2 and 3.
3. **Flop + Turn + River together** combine with AND; several labels within a street combine with OR. Pinned in Task 2.
4. **Checking a parent (`BP`, `BW`) on the page** sends its leaf labels, never the parent name, and disabled controls send nothing. Pinned by the Task 3 browser check.
5. **A lowercase label** (`"fc"`) is a 400 naming it. Pinned in Tasks 2 and 3.

---

### Task 0: Branch

- [ ] **Step 1:** `git checkout -b m7-runout-types`

### Task 1: `board_types.py` — runout labels

**Files:**
- Modify: `board_types.py`
- Test: `tests/test_board_types.py`

**Interfaces:**
- Produces: `TURN_LABELS: tuple[str, ...]`, `RIVER_LABELS: tuple[str, ...]`; `runout_labels(previous: list[tuple[str, str]], card: tuple[str, str], street: str) -> tuple[str, ...]` (`street` is `"t"` or `"r"`, labels in page order); `turn_labels(c1, c2, c3, c4) -> tuple[str, ...]` and `river_labels(c1, c2, c3, c4, c5) -> tuple[str, ...]` over PT4 card ids (decoded with `poker_cards.decode_card_id`, which raises outside 1–52).

- [ ] **Step 1: Write the failing tests**
  - Helper `parse("JdJcQc")` already exists for flops; reuse it for any length.
  - `TURN_FIXTURES` / `RIVER_FIXTURES`: every board in the spec appendix copied verbatim as `(previous, card, labels)`, e.g. `("Kc7cTh", "Jc", ("FC", "SC"))`, `("6h9d7s8s", "8h", ("BP mid",))`, plus the user's `("9s7c3h", "Kh", ("BW K", "FDP"))` and `("Js8d3h", "Qs", ("BW Q", "FDP"))` (Q-J-8 spans 4: not SC). Parametrized `test_turn_examples` / `test_river_examples`: `runout_labels(parse(prev), parse(card)[0], street) == labels` (exact tuple).
  - `test_sc_boundaries`: on `9s7d2c`, turn `8h` SC, `Th` SC, `5h` not SC; on `7s8d9c`, `Th` SC, `2h` not; on `Ks8d3c`, `9h` / `7h` / `6h` not SC; `3h` on `As2d9c` SC (A low); `Jh` on `AsKd4c` SC (A high); `9h` on `9s7d2c` not SC (pairs).
  - `test_bp_boundaries`: `7s7d2c` + `7h` → `BP high`, + `2h` → `BP low`; river `Ks9d6c3h` + `9s` and + `6s` → `BP mid`; `KsKdKc` style trips: `Ks9d9c` + `9h` → `BP low`.
  - `test_bw_boundaries`: `Ks8d3c` + `Kh` → `BP high`, no BW; `Ts8d3c` + `Th` no BW; river `Ks9d6c3h` + `Ah` → `BW A`, + `Qh` → no BW.
  - `test_invariants`: over 20,000 random (flop, turn) and 20,000 random (flop+turn, river) deals, `random.Random(0)`: Brick ⇔ none of FC/SC/BP */BW *; ≤ 1 BP label and ≤ 1 BW label; no FDP on the river; no BW together with a BP label.
  - `test_registries`: `TURN_LABELS` and `RIVER_LABELS` equal the Global Constraints tuples.
  - `test_ids_decode`: `turn_labels(52, 51, 50, 49) == ("FC", "SC")` (As Ks Qs + Js; J is not above A); `river_labels(1, 2, 3, 4, 0)` raises `ValueError`.

- [ ] **Step 2:** `venv/Scripts/python -m pytest tests/test_board_types.py -q`. Expected: ImportError on `TURN_LABELS` — so first add stubs (`TURN_LABELS = RIVER_LABELS = ()`, functions returning `()`), then re-run: assertion failures.

- [ ] **Step 3:** Implement per the Global Constraints rules.

- [ ] **Step 4:** Same command passes; full default suite green.

- [ ] **Step 5: Commit** — `feat(board_types): label turn and river cards`

### Task 2: `db` + `spotlight` — filter, columns, filter text

**Files:**
- Modify: `db.py` (`run_spot_query` SELECT), `spotlight.py` (`run_spot`, `describe`, `_with_flop_type`)
- Test: `tests/test_db.py`, `tests/test_spotlight.py`

**Interfaces:**
- Consumes: `TURN_LABELS`, `RIVER_LABELS`, `turn_labels`, `river_labels` (Task 1); `spec.decision.street` (`"f"`/`"t"`/`"r"`).
- Produces: `run_spot(pot, position, role, line, formations=(), date_from=None, date_to=None, flop_types=(), turn_types=(), river_types=())`; hand rows carry `turn_type` and `river_type` (str or `None`); `describe(..., flop_types=(), turn_types=(), river_types=())`.

- [ ] **Step 1: Write the failing tests**
  - `test_db.py::test_run_spot_query_builds_skeleton_and_binds_params`: assert `"chs.card_4, chs.card_5" in query`.
  - `test_spotlight.py`: `fake_matches` gains `card_4`, `card_5`: rows may carry a 4th element, a runout string `"Th"` or `"Th2c"`; default turn `2h`, river `0` (no river). Existing expected records gain `turn_type` / `river_type` as needed.
  - New:
    - `test_turn_filter_or_within_street`: `- B-?` (2bp ip pfr), three hands on flop `9s7c3h` with turns `Kh` (`BW K, FDP`), `8d` (`SC`), `2d` (`Brick`); `turn_types=["SC", "BW K"]` → hands {1, 2}.
    - `test_flop_turn_river_and` (Review Focus 3): river-decision Line `- B-B-?`; rows varying flop type, turn and river so that only one hand passes `flop_types=["BLL"]`, `turn_types=["Brick"]`, `river_types=["FC"]`.
    - `test_turn_decision_without_river` (Review Focus 1): `- B-?`, `card_5 = 0` → no error, every `river_type` is `None`, `turn_type` set.
    - `test_flop_decision_has_no_runout_columns_values`: `vs B?` → `turn_type` and `river_type` `None`, `card_4 = 0` does not raise.
    - `test_turn_types_need_turn_decision`, `test_river_types_need_river_decision` (Review Focus 2): `vs B?` + `turn_types=["FC"]` and `- B-?` + `river_types=["Brick"]` raise `SpotInputError`; `run_spot_query` not called.
    - `test_unknown_runout_label_raises` (Review Focus 5): `turn_types=["fc"]` → message contains `fc`; `river_types=["FDP"]` on a river Line also raises (FDP is turn-only).
    - `test_describe_runout_parts`: `· Turn type: FC, BP high ·` and `· River type: Brick ·` after the `Flop type` part, deduped; absent when empty.
    - `test_hand_columns_joined_in_page_order`: a hand with turn `Qc` on `Ts9h8d` has `turn_type == "SC, BW Q"`.

- [ ] **Step 2:** `venv/Scripts/python -m pytest tests/test_db.py tests/test_spotlight.py -q`. Expected: card_4 assert fails; new tests fail on the unexpected kwargs / missing columns.

- [ ] **Step 3: Implement**
  - `run_spot_query`: add `chs.card_4, chs.card_5` to the SELECT.
  - `run_spot`: dedupe and validate `turn_types` against `TURN_LABELS`, `river_types` against `RIVER_LABELS`, and the decision-street rule, all after `parse_line` and before the query. Generalize `_with_flop_type` into one board step that adds `flop_type`, `turn_type`, `river_type` (labels joined, `None` for an unlabeled street), filters each street with "any selected label in the card's labels", and drops `card_1..5`.
  - `describe`: the two new parts.

- [ ] **Step 4:** Full default suite green.

- [ ] **Step 5: Commit** — `feat(spotlight): filter by turn and river labels`

### Task 3: `/spot` + page

**Files:**
- Modify: `api.py` (`SpotRequest`, `spot`), `static/index.html` (bar markup, `spot-config`, JS, `COLUMNS`)
- Test: `tests/test_api.py`, `tests/test_static_config.py`

**Interfaces:**
- Consumes: `run_spot(..., turn_types=..., river_types=...)` (Task 2), `TURN_LABELS`, `RIVER_LABELS` (Task 1).
- Produces: `/spot` body fields `turn_types: list[str] = []`, `river_types: list[str] = []`.

- [ ] **Step 1: Write the failing tests**
  - `test_api.py`: fake `run_spot`s accept the new kwargs. `test_spot_passes_runout_types_through`, `test_spot_runout_types_default_to_empty`, `test_spot_unknown_turn_type_is_400` (real `run_spot`, `"fc"`), `test_spot_river_types_on_turn_line_is_400` (real `run_spot`, `- B-?`).
  - `test_static_config.py`: `load_config()["turn_types"] == list(TURN_LABELS)`, `["river_types"] == list(RIVER_LABELS)`.

- [ ] **Step 2:** `venv/Scripts/python -m pytest tests/test_api.py tests/test_static_config.py -q`. Expected: pass-through sees nothing; config KeyErrors.

- [ ] **Step 3: Implement**
  - `api.py`: both fields, passed through.
  - Page config: `"turn_types"`, `"river_types"` (leaf lists).
  - Two `<details class="formations">` after Flop, ids `turn-types`, `river-types`, summaries `Turn: Any` / `River: Any`. Extend `multiSelect` so leaves sharing a first word with another leaf (`BP …`, `BW …`) render under a parent checkbox of that word: checking it checks all children, it shows checked when all children are, its value is never returned. Summary collapses a fully checked group to its parent name (`Turn: FC, BP`).
  - Decision street from the Line text, same rule as `line_parser._split_tokens`: strip whitespace, drop the leading `-` / `vs`, count the `-`-separated tokens (1 flop, 2 turn, 3 river). On Line input, disable (`el` gets `disabled` styling, closed, checkboxes disabled) Turn when < 2 and River when < 3; `run()` sends `[]` for a disabled control.
  - `COLUMNS`: `Turn type` (`text("turn_type")`) after `Turn`, `River type` (`text("river_type")`) after `River`.

- [ ] **Step 4:** Default suite green. Browser check (restart uvicorn, Ctrl+F5):
  - `2bp IP PFR - B-?`: River disabled; Turn = Brick → every row's Turn type contains Brick; check `BP` → its three children checked, summary `Turn: BP`, rows all BP *.
  - `- B-B-?`: River enabled; Turn = FC + River = Brick → rows satisfy both.
  - `vs B?`: both disabled; columns show `—`.

- [ ] **Step 5: Commit** — `feat(page): turn and river filters`

### Task 4: `db` check on real hands

**Files:**
- Create: `tests/test_runout_types_db.py` (`pytestmark = pytest.mark.db`)

- [ ] **Step 1: Write the tests**
  - `test_turn_brick_vs_rest_partitions`: `run_spot("2bp", "ip", "pfr", "- B-?")`; hand ids for `["Brick"]` and for `["FC","SC","BP high","BP mid","BP low","BW A","BW K","BW Q","BW J"]` are disjoint and their union is the unfiltered set.
  - `test_river_brick_vs_rest_partitions`: same on `- B-B-?` with `river_types`.
  - `test_hand_column_contains_filtered_label`: for each turn label, every hand from `turn_types=[label]` has `label` in `turn_type.split(", ")`.
  - `test_all_labels_equals_any`: `turn_types=list(TURN_LABELS)` returns the unfiltered set.

- [ ] **Step 2:** `venv/Scripts/python -m pytest -m db -q`. These pin built behaviour; sabotage instead of red: make `Brick` also require "not FDP", confirm `test_turn_brick_vs_rest_partitions` still passes but `test_board_types.py::test_turn_examples` fails on the FDP + Brick fixtures; revert. Then make SC use span ≤ 4, confirm the SC boundary test fails; revert.

- [ ] **Step 3:** Sanity check (report, no test): each turn label's share on `- B-?` next to the spec's % table.

- [ ] **Step 4: Commit** — `test(db): runout labels on real Spotlight results`

### Task 5: Docs

- [ ] `CLAUDE.md`: `board_types.py` bullet covers runout labels; `run_spot_query` returns all 5 board cards; `run_spot` turn/river filters + columns; page Turn/River controls. Commit. Merge waits for the user.
