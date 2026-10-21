# Hand Strength on Turn and River Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Label, filter and break down Hero's made hand on turn and river decisions with the user's "hole cards must play" rules and a new `4th pair`.

**Architecture:** `hand_strength.classify_hand` takes a 3–5 card board and gains a five-card evaluator for the "beat the board" check and a two-highest-pairs rule; `hand_type` takes the board ids variadically. `spotlight` passes the decision street's board and drops the flop-only guard; the page enables `Hand` on every Line. The `db` oracle gains turn and river mappings.

**Tech Stack:** Python, pandas, pytest, vanilla JS.

**Spec:** `docs/superpowers/specs/2026-10-21-hand-strength-turn-river-design.md` (extends `docs/superpowers/specs/2026-10-21-hand-strength-flop-design.md`)

## Global Constraints

- `HAND_TYPES` = part 1 order with `"4th pair"` inserted between `"3rd pair"` and `"Underpair"`.
- Rule order (spec "What changes" §3): board-made (river, ≥ straight, Hero doesn't beat it) → No made hand; board quads → Ace high / No made hand; made hands; Set; Trips; pairs that play (two highest of P); Ace high; No made hand.
- "Beat" = full five-card comparison including kickers.
- Every part-1 flop fixture keeps its type.
- PT4 mismatch = stop point: show the hands to the user before changing rules or mapping.
- Inline comments one line max. Tests: `venv\Scripts\python -m pytest`.

## Review Focus

1. Flop behaviour unchanged — Task 1 keeps every part-1 fixture and Task 2 re-runs the flop oracle.
2. A turn decision must not read `card_5` (it is 0 for hands without a river) — Task 3 test with `card_5 = 0` on a turn Line.
3. Board straight on the river with Hero holding a lower straight card (4 on 56789) → No made hand — Task 1 fixture.
4. Double-paired board with a pocket pair below both pairs (33 on KK55) → No made hand, not Underpair — Task 1 fixture.
5. Stale `hand_split: None` assumptions in the page (`data.hand_split && …`) still work with `[]` — Task 4 browser check.

---

### Task 1: Classifier for 4- and 5-card boards

**Files:**
- Modify: `hand_strength.py`, `static/index.html` (`spot-config.hand_types` only)
- Test: `tests/test_hand_strength.py`

**Interfaces:**
- Produces: `HAND_TYPES` with `4th pair`; `classify_hand(hole, board)` for 3–5 board cards; `hand_type(holecard_1, holecard_2, *board_ids) -> str`.

- [ ] **Step 1: Write the failing tests**

`TURN_RIVER_EXAMPLES` parametrized like `USER_EXAMPLES`, one row per spec example (pick suits that create no accidental flush/straight; for "4x" use `4c2d`, for "any spade" `3s4d`, for "2s + non-spade" `2s4d`, for "A + x" `Ac7d`), exact type. Update `test_registry_order` with `4th pair`. Add `test_hand_type_takes_four_and_five_board_ids` (turn `Ac2d` on `Kh9s5d2c` → `4th pair`; river `Tc2d` on `5h6s7d8c9h` → `Straight`). Extend the invariant test to 3-, 4- and 5-card boards.

- [ ] **Step 2: Run** `venv\Scripts\python -m pytest tests/test_hand_strength.py -q` → new rows FAIL (wrong type / IndexError), flop rows PASS.

- [ ] **Step 3: Implement**

- `_rank5(cards) -> tuple` (category index, tie-break ranks) and `_best(cards) -> tuple` = max over 5-card combinations; categories ordered high card < pair < two pair < trips < straight < flush < full house < quads < straight flush; wheel straight high card = 5.
- In `classify_hand`, before the made-hand checks: if `len(board) == 5` and `_rank5(board)` is straight or better and `_best(hole + board) <= _rank5(board)` → `"No made hand"`; if the board holds four of a rank → `"Ace high"` if `"A"` in hole else `"No made hand"`.
- Quads only when a hole card is one of the four.
- Pairs: `P` = board pair ranks ∪ Hero pair ranks; a Hero pair plays iff in the two highest of `P`. Two pair needs both Hero pairs to play; else classify the higher playing Hero pair; none → fall through to Ace high / No made hand.
- `PAIR_POSITIONS` gains `"4th pair"`; position index capped at 3.
- `hand_type(holecard_1, holecard_2, *board)`.
- Page `spot-config.hand_types`: add `"4th pair"` (keeps `tests/test_static_config.py` green).

- [ ] **Step 4: Run** `venv\Scripts\python -m pytest -q` → all PASS.

- [ ] **Step 5: Commit** `feat(hand_strength): turn and river boards, 4th pair, hole cards must play`

### Task 2: Turn and river oracle (stop point)

**Files:** Modify `tests/test_hand_strength_db.py`, `docs/SCHEMA_NOTES.md`

- [ ] **Step 1:** Parametrize the `rows` fixture by street (`"f"`, `"t"`, `"r"`): board = `card_1..3/4/5`, `flg_<s>_saw`, `id_<s>_hand_strength`, `val_<s>_hole_cards_used`, `flg_<s>_*`. `allowed(street, category, strength, used)`: flop = part-1 mapping; turn/river = the spec's table (made categories with `used == 0` → Ace high / No made hand).
- [ ] **Step 2: Run** `venv\Scripts\python -m pytest tests/test_hand_strength_db.py -m db -q` → PASS. **Any mismatch: stop and bring the hands to the user.** Then a sabotage run (e.g. treat a non-playing pocket pair as Underpair) must produce mismatches.
- [ ] **Step 3:** `SCHEMA_NOTES.md` Session 64 section: turn/river mapping, hand counts, 0 mismatches, sabotage count.
- [ ] **Step 4: Commit** `test(db): hand types agree with PT4 on turn and river`

### Task 3: Spotlight on every decision street

**Files:** Modify `spotlight.py`, Test `tests/test_spotlight.py`, `tests/test_api.py`

**Interfaces:** Consumes `hand_type(h1, h2, *board)`. `hand_split` is always a list.

- [ ] **Step 1: Tests.** Replace `test_hand_types_need_a_flop_decision` with `test_hand_types_on_a_turn_decision` (RUNOUTS-style rows on `- B-?`, holes chosen to give two different types; filter keeps one). Replace `test_turn_decision_has_no_hand_type` with exact turn types; add a river Line case; `test_turn_decision_ignores_card_5` (row with `card_5 = 0`, no error). Replace `test_hand_split_none_on_turn_decision` with a turn `hand_split` rows test. `tests/test_api.py`: replace `test_spot_hand_types_on_turn_line_is_400` with an unknown-hand-type 400 test (`"Unknown hand type: x"`); `FAKE_RESULT["hand_split"] = []` and the shape test accordingly.
- [ ] **Step 2: Run** → the new tests FAIL.
- [ ] **Step 3: Implement.** `_with_hand_type` uses `card_1..3` / `..4` / `..5` by decision street (`{"f": 3, "t": 4, "r": 5}`); remove the flop-only guard; `hand_split` computed for every street.
- [ ] **Step 4: Run** `venv\Scripts\python -m pytest -q` → PASS.
- [ ] **Step 5: Commit** `feat(spotlight): hand types on turn and river decisions`

### Task 4: Page

**Files:** Modify `static/index.html`

- [ ] **Step 1:** Drop `selectedHandTypes.setEnabled(streets === 1)` (control always enabled).
- [ ] **Step 2:** `venv\Scripts\python -m pytest -q` → PASS. Browser: `2BP IP PFR - B-?` shows the hand table with `4th pair` possible and the Hand control enabled; `- B-B-?` (river) same; clicking a cell filters; `- ?` unchanged.
- [ ] **Step 3: Commit** `feat(page): hand types on every street`

### Task 5: Real-data Spotlight checks and docs

**Files:** Modify `tests/test_hand_strength_db.py`, `CLAUDE.md`

- [ ] **Step 1:** Parametrize the Spotlight `db` tests over `("2bp","oop","pfc","vs B?")`, `("2bp","ip","pfr","- B-?")`, `("2bp","ip","pfr","- B-B-?")`.
- [ ] **Step 2: Run** `venv\Scripts\python -m pytest -m db -q` → PASS (oracle 9/9 included).
- [ ] **Step 3:** `CLAUDE.md`: hand types on every decision street, `4th pair`, hole-cards-play rule, `hand_split` always a list.
- [ ] **Step 4: Commit** `test(db): hand types on turn and river Spotlight results; docs`
