# Hand Strength on the Flop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Label every flop-decision Spotlight hand with one hand type (the user's rules), filter by it, and show a hand type × action breakdown table.

**Architecture:** A pure `hand_strength.py` (like `board_types.py`) classifies Hero's hole cards + flop. `spotlight.run_spot` labels/filters right after the board types and builds `hand_split` from the existing `_distribution`. The page gets a `Hand` multi-select, the breakdown table and a `Hand type` column. A `db` test validates the classifier against PT4's `cash_hand_player_combinations` on every Hero flop hand.

**Tech Stack:** Python, pandas, FastAPI, pytest, vanilla JS (one file).

**Spec:** `docs/superpowers/specs/2026-10-21-hand-strength-flop-design.md`

## Global Constraints

- Hand type names, exact strings, priority = page = row order: `Straight flush`, `Quads`, `Full house`, `Flush`, `Straight`, `Set`, `Trips`, `Two pair`, `Overpair`, `Top pair`, `2nd pair`, `3rd pair`, `Underpair`, `Ace high`, `No made hand`. No `4th pair` in part 1.
- Hand types apply only when `spec.decision.street == "f"`; `hand_types` on a turn/river decision → `SpotInputError("Hand type needs a decision on the flop")`.
- Unknown hand type → `SpotInputError("Unknown hand type: <name>")` (via `_checked`).
- Interpreted filter part: `Hand: Top pair, Overpair`, placed after the River type part.
- Breakdown rows: only types with hands > 0. Cells = `_distribution` rows of that subset (size rows included on B/X; F/C/R on facing).
- One pick at a time across all tables on the page.
- Inline comments: one line max (user rule). Run tests with the venv: `venv\Scripts\python -m pytest`.

## Review Focus

1. Pocket pair on a paired flop (77 on JJ9, 44 on QQ6) must be Underpair, not 3rd pair — Task 1 fixtures pin it.
2. `get_hand_details` also returns `holecard_1/2`; merging must not create `_x/_y` columns — Task 3 drops them before the merge, test asserts `holecard_1` column is unique.
3. Empty result on a flop decision: `hand_split == []`, not `None`, and no crash — Task 4 test.
4. A Line with a turn decision plus a stale `Hand` selection on the page: control disabled → sends `[]` (multiSelect already returns `[]` when off) — Task 5 manual check.
5. Clicking `B` inside a hand row selects that type's `Bs…Bo` hands too — Task 5 manual check.

---

### Task 1: `hand_strength.py` classifier

**Files:**
- Create: `hand_strength.py`
- Test: `tests/test_hand_strength.py`

**Interfaces:**
- Consumes: `poker_cards.decode_card_id(card_id) -> (rank, suit)`; `board_types.RANKS`.
- Produces: `HAND_TYPES: tuple[str, ...]` (Global Constraints order); `classify_hand(hole, board) -> str` over `(rank, suit)` tuples; `hand_type(holecard_1, holecard_2, card_1, card_2, card_3) -> str` over PT4 card ids.

- [ ] **Step 1: Write the failing tests**

`test_user_examples` parametrized over every row of the spec's two fixture tables (user-confirmed + the five extra cases), exact type. Write cards as strings (`"Kh9s"`, `"JsJd9h"`); a `parse` helper like `tests/test_board_types.py:parse`. Where the spec gives ranks only, pick suits that make no flush (e.g. rainbow flop, offsuit hole); `6h5h` / `KhQh6s` and `AhQh` / `QhJh2h` keep their suits. Plus:

```python
def test_registry_order():
    assert HAND_TYPES == ("Straight flush", "Quads", "Full house", "Flush", "Straight", "Set", "Trips",
                          "Two pair", "Overpair", "Top pair", "2nd pair", "3rd pair", "Underpair",
                          "Ace high", "No made hand")

@pytest.mark.parametrize("hole, flop, type_", [
    ("AhKh", "QhJhTh", "Straight flush"), ("5h4h", "3h2hAh", "Straight flush"),  # A plays low
    ("AsAd", "AhAc2s", "Quads"), ("Ad2c", "AhAcAs", "Quads"),
    ("7c7d", "JsJd9h", "Underpair"), ("4c4d", "QsQd6h", "Underpair"),
    ("Ah5c", "4d3s2h", "Straight"), ("KcQd", "AhJsTd", "Straight"),
])
def test_priority_and_boundaries(hole, flop, type_): ...

def test_invariant_one_type_per_sample():
    # 20,000 random (hole, flop) deals, seed fixed: classify_hand returns a member of HAND_TYPES
    ...

def test_hand_type_decodes_pt4_ids():
    # card id = suit_index*13 + rank_index + 1, suits "cdhs" (see tests/test_spotlight.py:card_id)
    assert hand_type(card_id("Kh"), card_id("9s"), card_id("Js"), card_id("Jd"), card_id("9h")) == "2nd pair"
```
- [ ] **Step 2: Run to verify they fail**

Run: `venv\Scripts\python -m pytest tests/test_hand_strength.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'hand_strength'`.

- [ ] **Step 3: Implement in `hand_strength.py`**

`classify_hand(hole, board)` checks in priority order, first match wins. Ranks compared by `RANKS.index`; "distinct board ranks" sorted high to low; `pos(r)` = 1-based index in that list.

```
counts = Counter(all ranks of hole + board)
straight(ranks): 5 consecutive distinct values, A = 14 and 1
Straight flush : some suit has >= 5 cards and those cards' ranks are a straight
Quads          : max(counts) == 4
Full house     : a rank with count >= 3 and another with count >= 2
Flush          : some suit has >= 5 cards
Straight       : straight(all ranks)
Set            : pocket pair (h1 == h2) and h1 on board
Trips          : a hole rank r with board.count(r) == 2
Two pair       : h1 != h2, both on board
pocket pair p  : above = #distinct board ranks > p, below = #distinct < p
                 above == 0 -> Overpair; below == 0 -> Underpair; else ("2nd pair", "3rd pair")[above - 1]
one hole rank r on board -> ("Top pair", "2nd pair", "3rd pair")[pos(r) - 1]
"A" in hole    -> Ace high
else           -> No made hand
```

On a flop every made hand above Set uses a hole card (the board has 3 cards), so no "hole card used" check is needed in part 1. Keep the board length generic (no hard-coded 3); part 2 extends it.

- [ ] **Step 4: Run to verify they pass**

Run: `venv\Scripts\python -m pytest tests/test_hand_strength.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add hand_strength.py tests/test_hand_strength.py
git commit -m "feat(hand_strength): classify Hero's flop hand"
```

### Task 2: Validate the classifier against PT4 (stop point)

**Files:**
- Create: `tests/test_hand_strength_db.py` (marker `db`)
- Modify: `docs/SCHEMA_NOTES.md` (Session 64 section: validation result)

**Interfaces:**
- Consumes: `hand_strength.hand_type`, `db.engine`.

- [ ] **Step 1: Write the test**

One query, every Hero (`id_player = 10`) hand with `chps.flg_f_saw`: `chps.holecard_1/2`, `chs.card_1..3`, `c.id_f_hand_strength`, `c.val_f_hole_cards_used`, and a `category` from the flop flags (`CASE WHEN c.flg_f_strflush THEN 'strflush' WHEN c.flg_f_fouroak ... ELSE 'highcard' END`, strongest first), joining `cash_hand_player_combinations c` on `id_hand` + `id_player`. Use `sqlalchemy.text` (no `%` in the SQL anyway).

`allowed(category, strength, used) -> set[str]` encodes the spec's mapping table exactly (highcard / 1pair / 2pair / threeoak rows; straight, flush, fullhouse, fouroak, strflush → their type). An unmapped key returns `set()`.

```python
def test_every_flop_hand_agrees_with_pt4(rows):
    bad = rows[[hand_type(...) not in allowed(...) for ... in rows.itertuples()]]
    assert bad.empty, bad.head(20).to_string()   # shows hole, flop, PT4 code, our type

def test_every_hand_type_occurs(rows):
    # all 15 types except possibly "Straight flush" appear at least once
```

- [ ] **Step 2: Run it**

Run: `venv\Scripts\python -m pytest tests/test_hand_strength_db.py -m db -v`
Expected: PASS. **If any hand fails: stop.** Show the failing hands to the user (hole, flop, PT4 code, our type) before changing `hand_strength.py` or the mapping (spec: stop point).

- [ ] **Step 3: Record the result in `docs/SCHEMA_NOTES.md`**

Under "Hand strength per street (Session 64 spike)": the flop mapping is validated, N hands, 0 mismatches (or the explained exceptions). Replace "not yet validated against a PT4 export" accordingly.

- [ ] **Step 4: Commit**

```bash
git add tests/test_hand_strength_db.py docs/SCHEMA_NOTES.md
git commit -m "test(db): hand types agree with PT4 on every flop hand"
```

### Task 3: Spotlight filter, column and filter text

**Files:**
- Modify: `db.py` (`run_spot_query` SELECT), `spotlight.py`
- Test: `tests/test_db.py`, `tests/test_spotlight.py`

**Interfaces:**
- Consumes: `HAND_TYPES`, `hand_type` (Task 1).
- Produces: `run_spot(..., river_types=(), hand_types=())`; each hand gets `hand_type` (str on a flop decision, `None` otherwise); `describe(..., river_types=(), hand_types=())`.

- [ ] **Step 1: Write the failing tests**

- `tests/test_db.py::test_run_spot_query_builds_skeleton_and_binds_params`: add `assert "chps.holecard_1, chps.holecard_2" in query`.
- `tests/test_spotlight.py`: `fake_matches` rows gain an optional 5th element `hole` (default `"7h6h"`, No made hand on `Ks9d3c`), emitted as `holecard_1`, `holecard_2` columns. New tests:

```python
def test_hand_filter_or_within(monkeypatch):
    # hole "KcQd" (Top pair on Ks9d3c), "9c8c" (2nd pair), "7h6h" (No made hand)
    install(monkeypatch, fake_matches([(1, "Cs", BLL_FLOP, "2h", "KcQd"), (2, "Cs", BLL_FLOP, "2h", "9c8c"),
                                       (3, "Fs", BLL_FLOP, "2h", "7h6h")]))
    hands = spotlight.run_spot("2bp", "oop", "pfc", "vs B?", hand_types=["Top pair", "2nd pair"])["hands"]
    assert dict(zip(hands["id_hand"], hands["hand_type"])) == {1: "Top pair", 2: "2nd pair"}

def test_hand_and_flop_type(monkeypatch): ...      # flop_types + hand_types keep only hands matching both
def test_no_hand_types_keeps_every_hand(monkeypatch): ...
def test_hand_types_need_a_flop_decision(monkeypatch):
    with pytest.raises(SpotInputError, match="Hand type needs a decision on the flop"):
        spotlight.run_spot("2bp", "ip", "pfr", "- B-?", hand_types=["Top pair"])
def test_unknown_hand_type_raises(monkeypatch): ...   # match="Unknown hand type: Monster"
def test_turn_decision_has_no_hand_type(monkeypatch): ...  # "- B-?" -> hand_type column all None
def test_hole_cards_not_duplicated_by_details(monkeypatch):
    # details fake returns id_hand + holecard_1 + holecard_2; result has no holecard_1_x / _y columns
def test_describe_hand_part(): ...   # "... · River type: ... · Hand: Top pair, Overpair · Flop: ..." order
```

- [ ] **Step 2: Run to verify they fail**

Run: `venv\Scripts\python -m pytest tests/test_spotlight.py tests/test_db.py -v`
Expected: new tests FAIL (`unexpected keyword argument 'hand_types'`, missing holecard text); the rest PASS.

- [ ] **Step 3: Implement**

- `db.run_spot_query`: select `chps.holecard_1, chps.holecard_2` after `chs.card_5`.
- `spotlight.py`: `_checked(hand_types, HAND_TYPES, "hand type")`; the not-flop error next to the turn/river ones; a `_with_hand_type(matches, street, hand_types)` called right after `_with_board_types` that assigns `hand_type` (via `_board_column` over `holecard_1, holecard_2, card_1..3` on a flop decision, `None` otherwise), filters with `isin` when `hand_types`, and drops `holecard_1, holecard_2`. `_with_board_types` must then keep `card_1..3` until `_with_hand_type` has run (move the card drop after both).
- `describe`: `Hand: ...` part after `River type`.

- [ ] **Step 4: Run all non-db tests**

Run: `venv\Scripts\python -m pytest`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add db.py spotlight.py tests/test_db.py tests/test_spotlight.py
git commit -m "feat(spotlight): filter by hand type on flop decisions"
```

### Task 4: `hand_split` breakdown + API

**Files:**
- Modify: `spotlight.py`, `api.py`
- Test: `tests/test_spotlight.py`, `tests/test_api.py`

**Interfaces:**
- Consumes: `_distribution(labels, measured, prefix)`, `_pct`.
- Produces: `run_spot(...)["hand_split"]`: `None` unless flop decision, else `[{"hand_type": str, "hands": int, "pct_total": float, "cells": <_distribution rows of that type's hands>}]` in `HAND_TYPES` order, zero rows dropped. `POST /spot` takes `hand_types: list[str] = []` and returns `hand_split`.

- [ ] **Step 1: Write the failing tests**

```python
def test_hand_split_rows_cells_and_pcts(monkeypatch):
    # "- ?" style B/X flop decision: Line "- ?" with 2bp ip pfr; hands: Top pair Bs, Top pair X, No made hand X
    install(monkeypatch, fake_matches([(1, "Bs", BLL_FLOP, "2h", "KcQd"), (2, "X", BLL_FLOP, "2h", "KcQd"),
                                       (3, "X", BLL_FLOP, "2h", "7h6h")]))
    split = spotlight.run_spot("2bp", "ip", "pfr", "- ?")["hand_split"]
    assert [(r["hand_type"], r["hands"], r["pct_total"]) for r in split] == [
        ("Top pair", 2, 66.7), ("No made hand", 1, 33.3)]
    assert [(c["label"], c["hands"], c["pct"]) for c in split[0]["cells"]] == [
        ("B", 1, 50.0), ("Bs", 1, 50.0), ("Bm", 0, 0.0), ("Bl", 0, 0.0), ("Bo", 0, 0.0), ("X", 1, 50.0)]

def test_hand_split_facing_uses_unsized_cells(monkeypatch): ...  # "vs B?": cell labels ["XF","XC","XR"] (check label prefix against the existing distribution test)
def test_hand_split_none_on_turn_decision(monkeypatch): ...
def test_hand_split_empty_list_when_no_hands(monkeypatch): ...
```

Check the exact label set `_distribution` yields for the chosen Line against an existing test (`test_bet_splits_by_size_under_an_overall_row`) before fixing the expected values.

`tests/test_api.py`: every `fake_run_spot` accepts `hand_types` and returns `"hand_split": None`; new test that `hand_types` passes through and `hand_split` is in the response; `SpotInputError` from hand types → 400 (existing pattern).

- [ ] **Step 2: Run to verify they fail**

Run: `venv\Scripts\python -m pytest tests/test_spotlight.py tests/test_api.py -v`
Expected: new tests FAIL on `KeyError: 'hand_split'` / unexpected field.

- [ ] **Step 3: Implement**

`_hand_split(types, unsized, spec, prefix)` in `spotlight.py`, one row per type with hands > 0, `cells = _distribution(unsized[types == t], spec.measured, prefix)`; returned under `"hand_split"` (None when the decision isn't on the flop). `api.SpotRequest.hand_types: list[str] = []`, passed to `run_spot`, `"hand_split": result["hand_split"]` in the response.

- [ ] **Step 4: Run all non-db tests**

Run: `venv\Scripts\python -m pytest`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add spotlight.py api.py tests/test_spotlight.py tests/test_api.py
git commit -m "feat(spotlight): hand type breakdown"
```

### Task 5: Page — Hand control, breakdown table, Hand type column

**Files:**
- Modify: `static/index.html`
- Test: `tests/test_static_config.py`

**Interfaces:**
- Consumes: `hand_types` request field, `hand_split` response, `hand.hand_type` (Tasks 3–4).

- [ ] **Step 1: Write the failing test**

```python
def test_hand_types_match_the_backend():
    assert load_config()["hand_types"] == list(HAND_TYPES)
```

- [ ] **Step 2: Run it**

Run: `venv\Scripts\python -m pytest tests/test_static_config.py -v` → FAIL (`KeyError: 'hand_types'`).

- [ ] **Step 3: Implement the page**

- `spot-config`: `"hand_types"` in `HAND_TYPES` order. A `<details class="formations" id="hand-types">` after River, summary `Hand: Any`; `selectedHandTypes = multiSelect("hand-types", CONFIG.hand_types, v => "Hand: " + joinedOrAny(v))`, enabled only when `lineStreets(line) === 1` (in `refreshRunoutControls`); `hand_types` in the request body.
- Breakdown: `renderHandSplit(handSplit)` rendered after the distribution / facing split when `data.hand_split` is non-empty. Columns: `Hand type`, `Hands (% total)`, then one per cell of the first row (`cell.label`; cells with `parent` get the sub style). Cell = `pct%` + `<small>hands</small>`, `data-pick="hand:<type>|<label>"`; row header `data-pick="hand:<type>"`. Class `dist` so the existing click wiring and `.selected` styling apply.
- Picks: replace the inline membership test in `renderHands` with `matchesPick(hand, pick)`: a `hand:` pick splits into type and optional label and requires `hand.hand_type === type` plus, if a label, the existing label membership (`groupsOf[...] || [...]`).includes(label)); any other pick keeps today's behavior. One `activePick` for all tables (already global).
- `COLUMNS`: `{ label: "Hand type", render: text("hand_type") }` after `Flop type`.

- [ ] **Step 4: Run tests and check in the browser**

Run: `venv\Scripts\python -m pytest` → all PASS.
Then `venv\Scripts\python -m uvicorn api:app --port 8000`, open http://localhost:8000:
- `2BP IP PFR`, Line `- ?`: breakdown table shows only non-empty types with `B Bs Bm Bl Bo X` columns; clicking `Top pair × B` lists only top-pair bets of any size; clicking the `Top pair` header lists all top pairs; `Hand: Top pair` + Run narrows everything.
- Line `- B-?`: Hand control greyed out, no breakdown table, Hand type column empty.
- `2BP OOP PFC`, `vs B?`: facing split and hand breakdown both shown, F/C/R columns.

- [ ] **Step 5: Commit**

```bash
git add static/index.html tests/test_static_config.py
git commit -m "feat(page): hand type filter and breakdown"
```

### Task 6: Real-data checks and docs

**Files:**
- Modify: `tests/test_hand_strength_db.py`, `CLAUDE.md`

- [ ] **Step 1: Add Spotlight `db` tests** (pattern: `tests/test_flop_type_db.py`) on `("2bp", "oop", "pfc", "vs B?")`: single hand types partition the unfiltered result (hand ids and every distribution row); each filtered result's `hand_type` column equals its filter; all types = Any; the `hand_split` row counts sum to the result size.

- [ ] **Step 2: Run the db suite**

Run: `venv\Scripts\python -m pytest -m db -v`
Expected: all PASS, including `tests/test_spotlight_oracle.py` (9/9).

- [ ] **Step 3: `CLAUDE.md`**: add `hand_strength.py` to Architecture; `spotlight.py` bullet gains `hand_types` / `hand_split` / `hand_type`; `db.run_spot_query` returns the hole cards; page bullet mentions the Hand control and breakdown.

- [ ] **Step 4: Commit**

```bash
git add tests/test_hand_strength_db.py CLAUDE.md
git commit -m "test(db): hand types on real Spotlight results; docs"
```
