# Facing-bet Split (M7) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Line whose decision measures F / C / R with no size suffix on the decision street also returns a `split`: one row per size bucket with row-relative response frequencies, shown on the page as a 2D table under an "All" row.

**Architecture:** `spot_sql` appends the bucket letter to the measured letter (`F` → `Fs`) when `splits_by_size(spec)` holds, reusing the bound `Decimal` bucket CASE that already labels Hero's bets. `spotlight` collapses those labels back to F / C / R for the unchanged `distribution` and builds `split` from them. `api.py` passes `split` through; `index.html` renders the 2D table and filters hands by a label → groups map.

**Tech Stack:** Python 3, FastAPI, pandas, SQLAlchemy/psycopg2 over PT4 Postgres, pytest, vanilla JS.

**Spec:** `docs/superpowers/specs/2026-10-17-facing-split-design.md`

## Global Constraints

- Split applies iff `spec.measured == ("F", "C", "R")` **and** `spec.decision.size is None`. One predicate, `spot_sql.splits_by_size(spec)`, used by both `spot_sql` and `spotlight`.
- Bucket order and names come from `sizing.SIZE_BUCKETS` (S small, M medium, L large, O overbet); thresholds stay bound as `Decimal` params `bucket_S/M/L`, never interpolated.
- The WHERE keeps filtering on the bare letter (`substr(...) = ANY(%(measured)s)`); only `measured_sql` changes.
- `distribution` stays byte-identical to today for every Line (the `db` oracle and `test_spotlight.py` distribution tests stay green).
- `split` is `None` when it doesn't apply. Zero rows included; `pct_faced` = row / all hands; cell `pct` = cell / row hands; zero denominators give `0.0`; all pcts `round(..., 1)` floats.
- Inline comments: one line max (`feedback_comment_discipline`).
- Strict TDD: see each test fail for the expected reason before implementing.
- Branch `m7-facing-split`. Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Run tests with the venv: `venv/Scripts/python -m pytest ...` (Bash); `-m db` runs the Postgres tests.

## Review Focus

1. **A facing Line with zero matching hands** (e.g. a narrow formation + date range) must return four zero split rows, not a ZeroDivisionError or `null`. Pinned in Task 2.
2. **A facing Line with a decision suffix** (`vs Bs?`) must keep bare labels (`XF`) and `split: null`, so today's click filter keeps working. Pinned in Tasks 1 and 2.
3. **Facing a raise after Hero's cbet** (`- B?`, pfr) rows by Hero's cbet size and matches `- Bs?` exactly. Pinned in Task 3 (parametrized set equality).
4. **A turn decision after a sized flop** (`vs Bs-B?`): the flop's `size_f_*` bounds and the turn's `bucket_*` label coexist, sized on `chs.amt_pot_t`. Pinned in Task 1.
5. **Clicking an "All" cell after a split** must show every sized hand of that action (`XFs`…`XFo` under `XF`). Pinned in Task 4 (browser check; the groups map is the only mechanism).

---

### Task 0: Branch

- [ ] **Step 1:** `git checkout -b m7-facing-split`

### Task 1: `spot_sql` — sized facing label

**Files:**
- Modify: `spot_sql.py` (`_sized_bet_label`, `build_spot_query`, new `splits_by_size`)
- Test: `tests/test_spot_sql.py`

**Interfaces:**
- Produces: `splits_by_size(spec: LineSpec) -> bool`. `measured_sql` for a split Line evaluates to `'F'|'C'|'R'` + `'s'|'m'|'l'|'o'`.

- [ ] **Step 1: Write the failing tests** (replace `test_facing_decision_label_is_unchanged`; update `test_bet_decision_labels_bets_by_size` for the refactored CASE)

```python
LETTER_F = "substr(h_f.action, %(measure_pos)s, 1)"


def test_facing_decision_without_suffix_labels_the_response_by_size():
    where, params, measured_sql = build("2bp", "oop", "pfc", "vs B?")
    assert f"{LETTER_F} = ANY(%(measured)s)" in where  # filter on the letter, not the label
    assert measured_sql.startswith(f"{LETTER_F} || CASE ")
    for key in ("S", "M", "L"):
        assert f"< %(bucket_{key})s * chs.amt_pot_f THEN '{key.lower()}'" in measured_sql
    assert measured_sql.endswith("ELSE 'o' END")
    assert (params["bucket_S"], params["bucket_M"], params["bucket_L"]) == (
        Decimal("0.45"), Decimal("0.70"), Decimal("1.05"))


def test_facing_decision_with_suffix_label_stays_the_letter():
    _, params, measured_sql = build("2bp", "oop", "pfc", "vs Bs?")
    assert measured_sql == LETTER_F
    assert "bucket_S" not in params


def test_turn_split_after_a_sized_flop_keeps_both_bounds():
    _, params, measured_sql = build("2bp", "oop", "pfc", "vs Bs-B?")
    assert "size_f_lo" in params and "bucket_S" in params
    assert "* chs.amt_pot_t THEN 's'" in measured_sql


@pytest.mark.parametrize("line, role, position, expected", [
    ("vs B?", "pfc", "oop", True),
    ("- B?", "pfr", "ip", True),
    ("vs Bs?", "pfc", "oop", False),
    ("- B-?", "pfr", "ip", False),
])
def test_splits_by_size(line, role, position, expected):
    assert splits_by_size(parse_line(line, role, position)) is expected
```

In `test_bet_decision_labels_bets_by_size`, the assertions become: starts with `CASE WHEN {letter} = 'B' THEN 'B' || CASE `, contains `< %(bucket_{key})s * chs.amt_pot_t THEN '{key.lower()}'`, contains `ELSE 'o' END`, ends with `ELSE {letter} END`. Import `splits_by_size`.

- [ ] **Step 2:** `venv/Scripts/python -m pytest tests/test_spot_sql.py -v`. Expected: the new tests fail (ImportError on `splits_by_size` first; once stubbed, label assertions fail); the B test fails on `'B' || CASE`.

- [ ] **Step 3: Implement**
  - Rename `_sized_bet_label` → `_size_letter_sql(street, params) -> str`: the same CASE, but each branch yields the bare lowercase bucket letter (`THEN 's'`, `ELSE 'o'`).
  - B/X: `CASE WHEN {letter_sql} = 'B' THEN 'B' || {_size_letter_sql(...)} ELSE {letter_sql} END`.
  - `splits_by_size(spec)`: the Global Constraints predicate. When true, `measured_sql = f"{letter_sql} || {_size_letter_sql(d.street, params)}"`.

- [ ] **Step 4:** Same command. Expected: all `test_spot_sql.py` pass; then `venv/Scripts/python -m pytest` (full default suite) green.

- [ ] **Step 5: Commit** — `feat(spot_sql): label facing responses by bet size when the decision is unsized`

### Task 2: `spotlight` + `/spot` — `split` key

**Files:**
- Modify: `spotlight.py` (`run_spot`, new `_split`), `api.py` (`/spot` response)
- Test: `tests/test_spotlight.py`, `tests/test_api.py`

**Interfaces:**
- Consumes: `splits_by_size` (Task 1).
- Produces: `run_spot(...)["split"]` → `None` or `list[dict]`, each `{"size": "S", "name": "small", "hands": int, "pct_faced": float, "cells": [{"action": "F", "label": "XFs", "hands": int, "pct": float}, ...]}` (cells in F, C, R order). `/spot` JSON gains `"split"`. Hands' `measured_action` carries the full sized label (`XFs`).

- [ ] **Step 1: Write the failing tests** (`tests/test_spotlight.py`; the mocked DB now returns sized letters for `vs B?`, so update `test_distribution_counts_in_measured_order_with_zero_rows` and `test_hands_carry_the_label` inputs to `"Cs"`, `"Fm"` etc. with the **same expected distribution**, and expect hands `{7: "XCs", 8: "XFm"}`)

```python
def test_split_rows_in_bucket_order_with_row_relative_pct(monkeypatch):
    install(monkeypatch, fake_matches([(1, "Fs"), (2, "Cs"), (3, "Cs"), (4, "Rl")]))
    split = spotlight.run_spot("2bp", "oop", "pfc", "vs B?")["split"]
    assert [row["size"] for row in split] == ["S", "M", "L", "O"]
    assert split[0] == {"size": "S", "name": "small", "hands": 3, "pct_faced": 75.0, "cells": [
        {"action": "F", "label": "XFs", "hands": 1, "pct": 33.3},
        {"action": "C", "label": "XCs", "hands": 2, "pct": 66.7},
        {"action": "R", "label": "XRs", "hands": 0, "pct": 0.0},
    ]}
    assert split[1]["hands"] == 0 and [c["pct"] for c in split[1]["cells"]] == [0.0, 0.0, 0.0]
    assert split[2]["pct_faced"] == 25.0 and split[2]["cells"][2]["pct"] == 100.0


def test_split_with_zero_hands_has_four_zero_rows(monkeypatch):
    install(monkeypatch, fake_matches([]))
    split = spotlight.run_spot("2bp", "oop", "pfc", "vs B?")["split"]
    assert [(r["hands"], r["pct_faced"]) for r in split] == [(0, 0.0)] * 4


@pytest.mark.parametrize("line, role, position, rows", [
    ("vs Bs?", "pfc", "oop", [(1, "C")]),
    ("- B-?", "pfr", "ip", [(1, "Bs")]),
])
def test_split_is_none_when_not_applicable(monkeypatch, line, role, position, rows):
    install(monkeypatch, fake_matches(rows))
    assert spotlight.run_spot("2bp", position, role, line)["split"] is None
```

`tests/test_api.py`: add `"split": None` to `FAKE_RESULT` and to the expected JSON in `test_spot_returns_result_shape`; add `test_spot_passes_split_through` with a one-row split list asserting `response.json()["split"]` equals it.

- [ ] **Step 2:** `venv/Scripts/python -m pytest tests/test_spotlight.py tests/test_api.py -v`. Expected: KeyError `'split'` / distribution counts at 0 because `XCs` ≠ `XC`.

- [ ] **Step 3: Implement**
  - `run_spot`: `split = splits_by_size(spec)`. Feed `_distribution` the labels truncated to `len(prefix) + 1` when `split`, else as today; return `"split": _split(matches["measured_action"], prefix) if split else None`.
  - `_split(labels, prefix) -> list[dict]`: one row per `SIZE_BUCKETS` entry, cells for `("F", "C", "R")` with label `prefix + action + key.lower()`; total = `len(labels)`.
  - `api.py`: add `"split": result["split"]`.

- [ ] **Step 4:** Full default suite green: `venv/Scripts/python -m pytest`.

- [ ] **Step 5: Commit** — `feat(spotlight): split facing responses by bet size`

### Task 3: `db` checks — split agrees with the suffixed Lines

**Files:**
- Create: `tests/test_facing_split_db.py` (`pytestmark = pytest.mark.db`)

**Interfaces:**
- Consumes: `run_spot(...)` with `split` (Task 2).

- [ ] **Step 1: Write the tests**, parametrized over `SPOTS = [("2bp", "oop", "pfc", "vs B?"), ("2bp", "ip", "pfr", "- B?"), ("3bp", "ip", "pfc", "vs B-B?")]`:
  - `test_split_cells_sum_to_the_distribution`: for each action, `sum(row.cells[action].hands) == distribution[action].hands`, and `sum(row.hands) == len(hands)`.
  - `test_sized_labels_equal_the_suffixed_line(spot, key)` (also parametrized over `s m l o`): the suffixed Line is `line.replace("?", f"{key}?")`. For each action, the ids in the unsized result whose `measured_action == prefix + action + key` equal **exactly** the ids of the suffixed result whose `measured_action == prefix + action` (set equality, report extra/missing like the oracle).

- [ ] **Step 2:** `venv/Scripts/python -m pytest -m db -v`. Expected: the new tests and the existing oracle, sizing and date tests pass. These pin behaviour already built, so red isn't expected here; do the sabotage check instead: temporarily swap `'s'`/`'m'` in `_size_letter_sql`, confirm the equality test fails **on `s`/`m` cells**, then revert.

- [ ] **Step 3: Commit** — `test(db): facing split matches suffixed Lines by exact hand set`

### Task 4: Page — 2D split table

**Files:**
- Modify: `static/index.html` (`showResult`, `toggleLabel`, `renderHands`, `renderDistribution`, new `renderSplit`, CSS)

**Interfaces:**
- Consumes: `/spot` `split` (Task 2).

- [ ] **Step 1: Implement**
  - Replace `parentOf` with `groupsOf: label → [keys]`, built in `showResult`: from `distribution` rows with `parent`, `[label, parent]`; from `split` cells, `[cell.label, prefix+action, "size:" + row.size]`, where the All label is the `distribution` row with the same `action`. Hand filter: `!activeKey || (groupsOf[h.measured_action] || [h.measured_action]).includes(activeKey)`.
  - Clickable elements carry `data-key`; `toggleLabel(key)` toggles `.selected` on every `[data-key]` in the output.
  - With `split`: render `renderSplit(distribution, split)` instead of `renderDistribution` — header `Size | Hands (% faced) | <distribution labels>`; an "All" row (total hands, 100%, each cell `data-key` = the distribution label); then one row per size: the name cell has `data-key="size:S"`, each cell `data-key` = cell label. Cells show `pct.toFixed(1)%` with the hand count in a `<small>` line under it. Click targets are the cells (`td[data-key]`), not the whole row.
  - Without `split`: today's 1D table, unchanged except `data-label` → `data-key`.

- [ ] **Step 2: Browser check** (restart uvicorn, Ctrl+F5): `2bp OOP PFC vs B?` shows the 2D table with sizes small → overbet. Click `small × XC` → only `XCs` hands; click All `XF` → `XFs…XFo`; click `medium` → every medium hand; click again clears. `vs Bs?` and `- ?` render as before. `venv/Scripts/python -m pytest tests/test_static_config.py` green.

- [ ] **Step 3: Commit** — `feat(page): 2D facing-split table`

### Task 5: Docs + merge

- [ ] Update `CLAUDE.md` (spot_sql / spotlight / page bullets: sized facing labels, `split`, `splits_by_size`) and `docs/STATE.md` "Next". Commit, full suite + `-m db` green, merge `m7-facing-split` into `main` with `--no-ff`.
