# Spotlight UI (M5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the NL page with the Spotlight bar (toggles, typed Line with suggestions, multi-select Formations) over `POST /spot`, with `XF`/`XC`/`XR`-style labels, and validate it against PT4 exports.

**Architecture:** Backend first. `spot_sql` takes a list of formations (OR-ed, deduped, bound). `spotlight` lowercases the bar values and turns measured letters into labels (Hero's decision-street prefix + letter). `api` accepts `formations: list[str]`. Then `static/index.html` is rewritten as a single vanilla-JS page, with its presets and formations in a JSON `<script>` block that a pytest test checks against the backend. A small `pt4_diff.py` tool does the M5 `hand_no` diffs.

**Tech Stack:** Python 3, FastAPI, pandas, SQLAlchemy/psycopg2 over PT4 Postgres, pytest, vanilla HTML/JS.

**Spec:** `docs/superpowers/specs/2026-10-11-spotlight-design.md` (revised Session 59, commits `645393b`, `2bd7d8b`).

## Global Constraints

- Frontend: one file, `static/index.html`, vanilla HTML/JS, no framework, no build step.
- All SQL values go through parameter binding (`%(name)s` + `params`); never interpolate user values.
- Formations are OOP seat first; 6-max codes `SB` 9, `BB` 8, `UTG` 3, `MP` 2, `CO` 1, `BTN` 0; 15 pairs.
- `formations: []` (or omitted) = no seat condition; several = OR, pooled into one distribution.
- `label` = Hero's prefix on the decision street + measured action; with no prefix it equals `action`.
- `Ctrl+Enter` runs; plain `Enter` does not.
- Strict red-then-green TDD for every behavior change; inline comments one line max.
- Hero is `id_player = 10`.
- Validation is exact `hand_no` set membership (both directions), never a count match.
- Run tests with the venv: `venv\Scripts\python -m pytest ...` (PowerShell). DB tests: `-m db`.

## Review Focus

1. **Line typed under the wrong role** (user types `vs B?`, then flips to PFR and runs) → 400 with the parser message under the input, the Line is kept. Pinned in Task 3 (`test_spot_line_role_mismatch_is_400`) + Task 4 manual check 6.
2. **Bar values in another case via the API** (`"3BP"`, `"OOP"`) → same result as lowercase. Pinned in Task 2 (`test_bar_values_are_case_insensitive`).
3. **Duplicate formations, or a hand that could match two ticked pairs** → each hand counted once. Pinned in Task 1 (`test_duplicate_formations_bind_once`, DB `test_formations_pool_as_union_of_single_formations`).
4. **New Run while a distribution-row filter is active** → filter cleared, all hands shown, no row highlighted. Task 4 manual check 5.
5. **Two Runs in flight** (Ctrl+Enter twice fast, or change a toggle and rerun) → only the latest response renders. Request-id guard in Task 4 + manual check 9.

---

### Task 1: `spot_sql` takes a list of formations

**Files:**
- Modify: `spot_sql.py:31,53-60`
- Test: `tests/test_spot_sql.py`, `tests/test_spotlight_oracle.py`

**Interfaces:**
- Consumes: `line_parser.parse_line`, `SpotInputError`, existing `FORMATIONS`, `SEATS`.
- Produces: `build_spot_query(pot, position, role, spec, formations=()) -> (where_sql, params, measured_sql)`. `formations` is any iterable of pair strings; deduped in order; seat condition `(chps.position, v.position) IN ((%(hero_pos_0)s, %(villain_pos_0)s), ...)`; unknown pair → `SpotInputError("Unknown formation: <pair>")`.

- [ ] **Step 0: Branch**

```powershell
git checkout -b m5-spotlight-ui
```

- [ ] **Step 1: Write the failing tests**

In `tests/test_spot_sql.py`, change the helper and replace the three formation tests and the bad-values test (lines 6-8, 48-59, 68-75) with:

```python
def build(pot, position, role, line, formations=()):
    spec = parse_line(line, role, position)
    return build_spot_query(pot, position, role, spec, formations)
```

```python
@pytest.mark.parametrize("formations", [(), []])
def test_no_formation_adds_no_seat_condition(formations):
    where, params, _ = build("2bp", "ip", "pfr", "- B-?", formations)
    assert "chps.position" not in where
    assert "hero_pos_0" not in params


@pytest.mark.parametrize("position, hero_pos, villain_pos", [("oop", 8, 0), ("ip", 0, 8)])
def test_formation_maps_hero_seat_from_position(position, hero_pos, villain_pos):
    role, line = ("pfc", "vs B?") if position == "oop" else ("pfr", "- B-?")
    where, params, _ = build("2bp", position, role, line, ["BB vs BTN"])
    assert "(chps.position, v.position) IN ((%(hero_pos_0)s, %(villain_pos_0)s))" in where
    assert (params["hero_pos_0"], params["villain_pos_0"]) == (hero_pos, villain_pos)


def test_several_formations_are_ored():
    where, params, _ = build("2bp", "oop", "pfc", "vs B?", ["BB vs BTN", "BB vs CO"])
    assert (
        "(chps.position, v.position) IN ((%(hero_pos_0)s, %(villain_pos_0)s), "
        "(%(hero_pos_1)s, %(villain_pos_1)s))"
    ) in where
    assert (params["hero_pos_0"], params["villain_pos_0"]) == (8, 0)
    assert (params["hero_pos_1"], params["villain_pos_1"]) == (8, 1)


def test_duplicate_formations_bind_once():
    where, params, _ = build("2bp", "oop", "pfc", "vs B?", ["BB vs BTN", "BB vs BTN"])
    assert "hero_pos_1" not in params
    assert "%(hero_pos_1)s" not in where
```

```python
@pytest.mark.parametrize("pot, formations, message", [
    ("4bp", [], "Unknown pot: 4bp"),
    ("2bp", ["BTN vs BB"], "Unknown formation: BTN vs BB"),
    ("2bp", ["BB vs BTN", "XX"], "Unknown formation: XX"),
])
def test_bad_bar_values_raise(pot, formations, message):
    spec = parse_line("- B-?", "pfr", "ip")
    with pytest.raises(SpotInputError, match=message):
        build_spot_query(pot, "ip", "pfr", spec, formations)
```

Append to `tests/test_spotlight_oracle.py` (DB, marker already set module-wide):

```python
def test_formations_pool_as_union_of_single_formations():
    spec = parse_line("vs B?", "pfc", "oop")

    def hands(formations):
        where, params, measured_sql = build_spot_query("2bp", "oop", "pfc", spec, formations)
        return set(run_spot_query(where, params, measured_sql)["id_hand"])

    btn, co = hands(["BB vs BTN"]), hands(["BB vs CO"])
    assert btn and co and not (btn & co)
    assert hands(["BB vs BTN", "BB vs CO"]) == btn | co
```

- [ ] **Step 2: Run to verify they fail**

Run: `venv\Scripts\python -m pytest tests/test_spot_sql.py -v`
Expected: FAIL. The list-taking tests raise `SpotInputError: Unknown formation: ['BB vs BTN'] (write the OOP seat first)` (a list is not `in FORMATIONS`); `test_no_formation_adds_no_seat_condition[formations0]` fails the same way for `()`. If any fails for another reason, stop and find out why.

- [ ] **Step 3: Implement**

In `spot_sql.py`, change the signature and replace the `if formation is not None:` block:

```python
def build_spot_query(pot, position, role, spec, formations=()):
```

```python
    selected = list(dict.fromkeys(formations))  # dedupe, keep order
    unknown = [f for f in selected if f not in FORMATIONS]
    if unknown:
        raise SpotInputError(f"Unknown formation: {unknown[0]}")
    if selected:
        pairs = []
        for i, formation in enumerate(selected):
            oop_seat, ip_seat = formation.split(" vs ")
            hero_seat, villain_seat = (oop_seat, ip_seat) if position == "oop" else (ip_seat, oop_seat)
            pairs.append(f"(%(hero_pos_{i})s, %(villain_pos_{i})s)")
            params[f"hero_pos_{i}"] = SEATS[hero_seat]
            params[f"villain_pos_{i}"] = SEATS[villain_seat]
        where += f" AND (chps.position, v.position) IN ({', '.join(pairs)})"
```

- [ ] **Step 4: Run to verify they pass**

Run: `venv\Scripts\python -m pytest tests/test_spot_sql.py -v` → all PASS.
Run: `venv\Scripts\python -m pytest -m db tests/test_spotlight_oracle.py -v` → 10 PASS (9 oracle + the union test). Postgres must be up.

- [ ] **Step 5: Commit**

```powershell
git add spot_sql.py tests/test_spot_sql.py tests/test_spotlight_oracle.py
git commit -m "spot_sql: formations as a deduped, OR-ed list"
```

---

### Task 2: `spotlight` labels, case-insensitive bar values, formations list

**Files:**
- Modify: `spotlight.py`
- Test: `tests/test_spotlight.py`

**Interfaces:**
- Consumes: `build_spot_query(pot, position, role, spec, formations=())` from Task 1.
- Produces:
  - `run_spot(pot, position, role, line, formations=()) -> {"interpreted_filter": str, "distribution": list[dict], "hands": DataFrame}`. `pot`/`position`/`role` any case.
  - Distribution rows: `{"action", "label", "name", "hands", "pct"}`; `pct` is a Python `float`.
  - `hands["measured_action"]` holds the label (`"XC"`), not the bare letter.
  - `describe(pot, position, role, formations, spec, n_hands) -> str`; `formations` a list; empty → `Any`; several joined with `", "`; "measuring" uses labels.

- [ ] **Step 1: Write the failing tests**

In `tests/test_spotlight.py`, replace `test_distribution_counts_in_measured_order_with_zero_rows`, `test_hands_carry_measured_action`, and both `describe` tests with:

```python
def test_distribution_counts_in_measured_order_with_zero_rows(monkeypatch):
    install(monkeypatch, fake_matches([(1, "C"), (2, "C"), (3, "F")]))
    result = spotlight.run_spot("2bp", "oop", "pfc", "vs B?")
    assert result["distribution"] == [
        {"action": "F", "label": "XF", "name": "Fold", "hands": 1, "pct": 33.3},
        {"action": "C", "label": "XC", "name": "Call", "hands": 2, "pct": 66.7},
        {"action": "R", "label": "XR", "name": "Raise", "hands": 0, "pct": 0.0},
    ]
    assert all(type(row["pct"]) is float for row in result["distribution"])


def test_hands_carry_the_label(monkeypatch):
    install(monkeypatch, fake_matches([(7, "C"), (8, "F")]))
    hands = spotlight.run_spot("2bp", "oop", "pfc", "vs B?")["hands"]
    assert dict(zip(hands["id_hand"], hands["measured_action"])) == {7: "XC", 8: "XF"}


def test_label_equals_action_without_prefix(monkeypatch):
    install(monkeypatch, fake_matches([(7, "B"), (8, "X")]))
    result = spotlight.run_spot("2bp", "ip", "pfr", "- B-?")
    assert [row["label"] for row in result["distribution"]] == ["B", "X"]
    assert dict(zip(result["hands"]["id_hand"], result["hands"]["measured_action"])) == {7: "B", 8: "X"}


def test_bar_values_are_case_insensitive(monkeypatch):
    install(monkeypatch, fake_matches([(1, "C")]))
    result = spotlight.run_spot("2BP", "OOP", "PFC", "vs B?")
    assert result["interpreted_filter"].startswith("2BP · OOP · PFC · Any · ")


def test_duplicate_formations_show_once(monkeypatch):
    install(monkeypatch, fake_matches([(1, "C")]))
    text = spotlight.run_spot("2bp", "oop", "pfc", "vs B?", ["BB vs BTN", "BB vs BTN"])["interpreted_filter"]
    assert "· BB vs BTN · " in text


def test_describe_reads_like_the_bar():
    spec = parse_line("- B-?", "pfr", "ip")
    text = spotlight.describe("2bp", "ip", "pfr", ["BB vs BTN"], spec, 1204)
    assert text == "2BP · IP · PFR · BB vs BTN · Flop: Hero B, villain XC · Turn: villain X, measuring B / X · 1,204 hands"


def test_describe_without_formation_says_any():
    spec = parse_line("vs B?", "pfc", "oop")
    text = spotlight.describe("3bp", "oop", "pfc", [], spec, 5)
    assert text == "3BP · OOP · PFC · Any · Flop: Hero X, villain B, measuring XF / XC / XR · 5 hands"


def test_describe_joins_several_formations():
    spec = parse_line("vs B?", "pfc", "oop")
    text = spotlight.describe("2bp", "oop", "pfc", ["BB vs BTN", "BB vs CO"], spec, 2668)
    assert text.startswith("2BP · OOP · PFC · BB vs BTN, BB vs CO · Flop: ")
```

(`test_zero_hands_skips_detail_query_and_returns_empty` and `test_nan_in_hand_details_becomes_none` stay as they are; with `- B-?` the label equals the letter.)

- [ ] **Step 2: Run to verify they fail**

Run: `venv\Scripts\python -m pytest tests/test_spotlight.py -v`
Expected: FAIL. Distribution rows lack `label`; hands hold `C` not `XC`; `run_spot("2BP", ...)` raises `SpotInputError: Unknown role: PFC`; `describe` with a list renders `['BB vs BTN']`; "measuring F / C / R" instead of labels.

- [ ] **Step 3: Implement**

Replace `describe`, `_distribution` and `run_spot` in `spotlight.py`:

```python
def describe(pot, position, role, formations, spec, n_hands):
    parts = [pot.upper(), position.upper(), role.upper(), ", ".join(formations) or "Any"]
    for s in spec.completed:
        parts.append(f"{STREET_NAMES[s.street].capitalize()}: Hero {s.hero}, villain {s.villain}")
    d = spec.decision
    seen = [f"Hero {d.hero}"] * bool(d.hero) + [f"villain {d.villain}"] * bool(d.villain)
    measuring = "measuring " + " / ".join(d.hero + action for action in spec.measured)
    parts.append(f"{STREET_NAMES[d.street].capitalize()}: " + ", ".join(seen + [measuring]))
    parts.append(f"{n_hands:,} hands")
    return " · ".join(parts)


def _distribution(labels, measured, prefix):
    counts = labels.value_counts()
    total = int(counts.sum())
    rows = []
    for action in measured:
        label = prefix + action
        hands = int(counts.get(label, 0))
        rows.append({
            "action": action,
            "label": label,
            "name": ACTION_NAMES[action],
            "hands": hands,
            "pct": round(hands / total * 100, 1) if total else 0.0,
        })
    return rows


def run_spot(pot, position, role, line, formations=()):
    pot, position, role = pot.lower(), position.lower(), role.lower()
    formations = list(dict.fromkeys(formations))
    spec = parse_line(line, role, position)
    where, params, measured_sql = build_spot_query(pot, position, role, spec, formations)
    matches = run_spot_query(where, params, measured_sql)
    prefix = spec.decision.hero
    matches = matches.assign(measured_action=prefix + matches["measured_action"])  # letter -> label

    if matches.empty:
        hands = pd.DataFrame()  # nothing to render, skip the detail round-trip
    else:
        hands = get_hand_details(matches["id_hand"]).merge(matches, on="id_hand", how="left")
        hands = hands.astype(object).where(hands.notna(), None)

    return {
        "interpreted_filter": describe(pot, position, role, formations, spec, len(matches)),
        "distribution": _distribution(matches["measured_action"], spec.measured, prefix),
        "hands": hands,
    }
```

- [ ] **Step 4: Run to verify they pass**

Run: `venv\Scripts\python -m pytest tests/test_spotlight.py -v` → all PASS.

- [ ] **Step 5: Commit**

```powershell
git add spotlight.py tests/test_spotlight.py
git commit -m "spotlight: decision labels (XF/XC/XR), case-insensitive bar, formations list"
```

---

### Task 3: `POST /spot` takes `formations`

**Files:**
- Modify: `api.py:55-73`, `CLAUDE.md` (Architecture bullets for `spot_sql.py` and `spotlight.py`)
- Test: `tests/test_api.py:80-119`

**Interfaces:**
- Consumes: `run_spot(pot, position, role, line, formations=())` from Task 2.
- Produces: request body `{"pot", "position", "role", "line", "formations": [str]}`; `formations` defaults to `[]`. Response unchanged in shape except distribution rows now carry `label`.

- [ ] **Step 1: Write the failing tests**

In `tests/test_api.py`, replace from `SPOT_BODY` to the end of `test_spot_input_error_is_400_with_message`, and add two tests:

```python
SPOT_BODY = {"pot": "2bp", "position": "ip", "role": "pfr", "line": "- B-?", "formations": []}


def install_fake_run_spot(monkeypatch, result):
    calls = []

    def fake_run_spot(pot, position, role, line, formations=()):
        calls.append((pot, position, role, line, formations))
        return result

    monkeypatch.setattr("api.run_spot", fake_run_spot)
    return calls


FAKE_RESULT = {
    "interpreted_filter": "2BP · IP · PFR · Any · ...",
    "distribution": [{"action": "B", "label": "B", "name": "Bet", "hands": 1, "pct": 100.0}],
    "hands": pd.DataFrame({"id_hand": [1], "measured_action": ["B"]}),
}


def test_spot_returns_result_shape(monkeypatch):
    calls = install_fake_run_spot(monkeypatch, FAKE_RESULT)
    response = client.post("/spot", json=SPOT_BODY)
    assert response.status_code == 200
    assert response.json() == {
        "interpreted_filter": "2BP · IP · PFR · Any · ...",
        "distribution": [{"action": "B", "label": "B", "name": "Bet", "hands": 1, "pct": 100.0}],
        "hands": [{"id_hand": 1, "measured_action": "B"}],
    }
    assert calls == [("2bp", "ip", "pfr", "- B-?", [])]


def test_spot_passes_formations_through(monkeypatch):
    calls = install_fake_run_spot(monkeypatch, FAKE_RESULT)
    client.post("/spot", json=SPOT_BODY | {"formations": ["BB vs BTN", "BB vs CO"]})
    assert calls[0][4] == ["BB vs BTN", "BB vs CO"]


def test_spot_formations_default_to_empty(monkeypatch):
    calls = install_fake_run_spot(monkeypatch, FAKE_RESULT)
    body = {k: v for k, v in SPOT_BODY.items() if k != "formations"}
    client.post("/spot", json=body)
    assert calls[0][4] == []


def test_spot_input_error_is_400_with_message(monkeypatch):
    def fake_run_spot(*args, **kwargs):
        raise SpotInputError("Unknown formation: BTN vs BB")

    monkeypatch.setattr("api.run_spot", fake_run_spot)
    response = client.post("/spot", json=SPOT_BODY | {"formations": ["BTN vs BB"]})
    assert response.status_code == 400
    assert response.json() == {"error": "Unknown formation: BTN vs BB"}


def test_spot_line_role_mismatch_is_400():
    response = client.post("/spot", json=SPOT_BODY | {"line": "vs B?"})
    assert response.status_code == 400
    assert response.json() == {"error": "With PFR the Line starts with '-' (your letters)"}
```

(`test_spot_real_parser_error_is_400` stays. `test_spot_line_role_mismatch_is_400` hits the real parser, which raises before any DB call.)

- [ ] **Step 2: Run to verify they fail**

Run: `venv\Scripts\python -m pytest tests/test_api.py -v`
Expected: FAIL. `api.spot` still passes `request.formation` (None, the field doesn't exist in the body → pydantic default) so `calls` holds `None` instead of `[]` / the list. `test_spot_line_role_mismatch_is_400` should already PASS (it pins existing behavior); confirm it does.

- [ ] **Step 3: Implement**

In `api.py`:

```python
class SpotRequest(BaseModel):
    pot: str
    position: str
    role: str
    line: str
    formations: list[str] = []


@app.post("/spot")
def spot(request: SpotRequest):
    try:
        result = run_spot(request.pot, request.position, request.role, request.line, request.formations)
    except SpotInputError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    return {
        "interpreted_filter": result["interpreted_filter"],
        "distribution": result["distribution"],
        "hands": result["hands"].to_dict(orient="records"),
    }
```

In `CLAUDE.md`, replace the `spot_sql.py` and `spotlight.py` bullets with:

```markdown
- **`spot_sql.py`**: `build_spot_query(pot, position, role, spec, formations=()) -> (where_sql, params, measured_sql)`. `PREFLOP_CONTEXTS` (pot × role) reuses validated `ATOMIC_FILTERS`; `FORMATIONS` are OOP-first seat pairs over `SEATS` (6-max codes). Selected formations are deduped and OR-ed as `(chps.position, v.position) IN (...)`, every seat bound.
- **`spotlight.py`**: `run_spot(...)` lowercases pot/position/role, orchestrates, and builds the distribution (measured-set order, zero rows included) and the interpreted-filter text (`describe`). Each distribution row and each hand's `measured_action` carry a **label**: Hero's decision-street prefix + the measured letter (`XF`/`XC`/`XR`; `B`/`X` with no prefix). Empty results skip `get_hand_details`; NaN → `None`.
```

- [ ] **Step 4: Run the whole default suite**

Run: `venv\Scripts\python -m pytest`
Expected: all PASS (db tests deselected).

- [ ] **Step 5: Commit**

```powershell
git add api.py tests/test_api.py CLAUDE.md
git commit -m "api: /spot takes a formations list"
```

---

### Task 4: Spotlight page

**Files:**
- Rewrite: `static/index.html`
- Create: `tests/test_static_config.py`
- Modify: `CLAUDE.md` (Project scope paragraph; `static/index.html` mention in the NL data-flow line)

**Interfaces:**
- Consumes: `POST /spot` from Task 3 (body `{pot, position, role, line, formations}`; 200 `{interpreted_filter, distribution[{action,label,name,hands,pct}], hands[...]}`; 400 `{error}`); `spot_sql.FORMATIONS`; `line_parser.parse_line`.
- Produces: the page. Its presets and formations live in `<script type="application/json" id="spot-config">`, keyed `"presets"` (`"<pot> <position> <role>"` → list of Lines) and `"formations"` (list, same order as `spot_sql.FORMATIONS`).

- [ ] **Step 1: Write the failing config test**

Create `tests/test_static_config.py`:

```python
import json
import re
from pathlib import Path

from line_parser import parse_line
from spot_sql import FORMATIONS

INDEX = Path(__file__).resolve().parent.parent / "static" / "index.html"


def load_config():
    html = INDEX.read_text(encoding="utf-8")
    match = re.search(r'<script type="application/json" id="spot-config">(.*?)</script>', html, re.S)
    assert match, "index.html has no spot-config block"
    return json.loads(match.group(1))


def test_formations_match_the_backend():
    assert load_config()["formations"] == FORMATIONS


def test_presets_are_the_20_v1_lines_and_all_parse():
    presets = load_config()["presets"]
    assert sum(len(lines) for lines in presets.values()) == 20
    for context, lines in presets.items():
        pot, position, role = context.split()
        assert pot in ("2bp", "3bp")
        for line in lines:
            parse_line(line, role, position)  # raises SpotInputError if a preset is malformed
```

- [ ] **Step 2: Run to verify it fails**

Run: `venv\Scripts\python -m pytest tests/test_static_config.py -v`
Expected: FAIL with `AssertionError: index.html has no spot-config block`.

- [ ] **Step 3: Rewrite `static/index.html`**

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Spotlight</title>
  <style>
    body { font-family: sans-serif; margin: 2rem auto; padding: 0 1.5rem; max-width: 1800px; }
    .bar { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: flex-start; }
    .seg { display: inline-flex; }
    .seg button { padding: 0.4rem 0.8rem; border: 1px solid #bbb; background: #fff; cursor: pointer; font-size: 0.95rem; }
    .seg button + button { border-left: none; }
    .seg button.on { background: #2b5fab; color: #fff; border-color: #2b5fab; }
    .seg button:disabled { color: #aaa; cursor: not-allowed; }
    .line-box { display: flex; flex-direction: column; }
    #line { width: 14rem; padding: 0.4rem; font-size: 1rem; font-family: monospace; }
    #line-error { color: #b3261e; font-size: 0.85rem; margin-top: 0.25rem; min-height: 1rem; max-width: 28rem; }
    details.formations { position: relative; }
    details.formations summary { list-style: none; padding: 0.4rem 0.8rem; border: 1px solid #bbb; cursor: pointer; min-width: 9rem; max-width: 22rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    details.formations summary::after { content: " ▾"; }
    details.formations .panel { position: absolute; z-index: 10; background: #fff; border: 1px solid #bbb; padding: 0.4rem 0.6rem; max-height: 24rem; overflow-y: auto; }
    details.formations label { display: block; padding: 0.15rem 0; white-space: nowrap; cursor: pointer; }
    #run { padding: 0.4rem 1rem; font-size: 1rem; }
    #output { margin-top: 1.25rem; }
    .filter-line { font-weight: bold; margin-bottom: 0.75rem; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 1rem; font-size: 0.78rem; }
    th, td { border: 1px solid #ddd; padding: 0.25rem 0.4rem; text-align: left; white-space: nowrap; }
    th { background: #f4f4f4; }
    tr:nth-child(even) { background: #fafafa; }
    table.dist { width: auto; font-size: 0.95rem; }
    table.dist tbody tr { cursor: pointer; }
    table.dist tbody tr:hover { background: #eef3fb; }
    table.dist tbody tr.selected { background: #dbe7f8; font-weight: bold; }
    .table-scroll { overflow-x: auto; }
    .wrap { white-space: normal; max-width: 14rem; }
    .error { background: #fdecea; border: 1px solid #f5c2c0; padding: 0.75rem; border-radius: 4px; }
    .card { display: inline-block; padding: 0 4px; margin: 0 1px; border: 1px solid #ccc; border-radius: 3px; background: #fff; font-weight: bold; }
    .card-red { color: #d32f2f; }
    .card-black { color: #222; }
  </style>
</head>
<body>
  <h1>Spotlight</h1>
  <div class="bar">
    <div class="seg" data-key="pot">
      <button data-value="limp" disabled>LIMP</button>
      <button data-value="2bp" class="on">2BP</button>
      <button data-value="3bp">3BP</button>
      <button data-value="4bp" disabled>4BP</button>
    </div>
    <div class="seg" data-key="position">
      <button data-value="oop" class="on">OOP</button>
      <button data-value="ip">IP</button>
    </div>
    <div class="seg" data-key="role">
      <button data-value="pfc" class="on">PFC</button>
      <button data-value="pfr">PFR</button>
    </div>
    <div class="line-box">
      <input id="line" list="line-presets" placeholder="Line, e.g. vs B?" autocomplete="off" spellcheck="false">
      <datalist id="line-presets"></datalist>
      <div id="line-error"></div>
    </div>
    <details class="formations" id="formations">
      <summary id="formations-summary">Any</summary>
      <div class="panel" id="formations-panel"></div>
    </details>
    <button id="run" disabled>Run</button>
  </div>
  <div id="output"></div>

  <script type="application/json" id="spot-config">
  {
    "presets": {
      "2bp oop pfc": ["vs B?", "vs B-X-?", "vs X-C-?"],
      "2bp ip pfc": ["vs B?", "vs X?"],
      "3bp oop pfc": ["vs B?", "vs B-X-?"],
      "3bp ip pfc": ["vs B?", "vs B-B?", "vs B-XC-X?"],
      "2bp oop pfr": ["- B-?", "- X-B-?"],
      "2bp ip pfr": ["- B-?", "- B-B-?", "- X-B-?"],
      "3bp oop pfr": ["- B-?", "- B-B-?", "- B-X-?"],
      "3bp ip pfr": ["- B-?", "- B-B-?"]
    },
    "formations": [
      "SB vs BB", "SB vs UTG", "SB vs MP", "SB vs CO", "SB vs BTN",
      "BB vs UTG", "BB vs MP", "BB vs CO", "BB vs BTN",
      "UTG vs MP", "UTG vs CO", "UTG vs BTN",
      "MP vs CO", "MP vs BTN",
      "CO vs BTN"
    ]
  }
  </script>

  <script>
    const CONFIG = JSON.parse(document.getElementById("spot-config").textContent);
    const state = { pot: "2bp", position: "oop", role: "pfc" };

    const barEl = document.querySelector(".bar");
    const lineEl = document.getElementById("line");
    const lineErrorEl = document.getElementById("line-error");
    const presetsEl = document.getElementById("line-presets");
    const formationsEl = document.getElementById("formations");
    const formationsSummaryEl = document.getElementById("formations-summary");
    const formationsPanelEl = document.getElementById("formations-panel");
    const runEl = document.getElementById("run");
    const outputEl = document.getElementById("output");

    let latestRequest = 0;
    let currentHands = [];
    let activeLabel = null;

    function escapeHtml(str) {
      const div = document.createElement("div");
      div.textContent = str;
      return div.innerHTML;
    }

    // --- Bar ---

    document.querySelectorAll(".seg").forEach(seg => {
      seg.addEventListener("click", event => {
        const button = event.target.closest("button");
        if (!button || button.disabled) return;
        state[seg.dataset.key] = button.dataset.value;
        seg.querySelectorAll("button").forEach(b => b.classList.toggle("on", b === button));
        refreshPresets();
      });
    });

    function refreshPresets() {
      const lines = CONFIG.presets[`${state.pot} ${state.position} ${state.role}`] || [];
      presetsEl.replaceChildren(...lines.map(line => {
        const option = document.createElement("option");
        option.value = line;
        return option;
      }));
    }

    CONFIG.formations.forEach(formation => {
      const label = document.createElement("label");
      const box = document.createElement("input");
      box.type = "checkbox";
      box.value = formation;
      label.append(box, " " + formation);
      formationsPanelEl.append(label);
    });

    function selectedFormations() {
      return [...formationsPanelEl.querySelectorAll("input:checked")].map(box => box.value);
    }

    formationsPanelEl.addEventListener("change", () => {
      const selected = selectedFormations();
      formationsSummaryEl.textContent = selected.length ? selected.join(", ") : "Any";
    });

    document.addEventListener("click", event => {
      if (!formationsEl.contains(event.target)) formationsEl.open = false;
    });

    lineEl.addEventListener("input", () => {
      runEl.disabled = !lineEl.value.trim();
    });

    barEl.addEventListener("keydown", event => {
      if (event.key === "Enter" && (event.ctrlKey || event.metaKey) && !runEl.disabled) {
        event.preventDefault();
        run();
      }
    });

    runEl.addEventListener("click", run);

    // --- Request ---

    async function run() {
      const requestId = ++latestRequest;
      const body = { ...state, line: lineEl.value.trim(), formations: selectedFormations() };
      lineErrorEl.textContent = "";
      outputEl.innerHTML = "Consultando...";

      try {
        const response = await fetch("/spot", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        const data = await response.json();
        if (requestId !== latestRequest) return;  // a newer Run superseded this one
        if (response.status === 400) {
          lineErrorEl.textContent = data.error;
          outputEl.innerHTML = "";
        } else if (!response.ok) {
          outputEl.innerHTML = `<div class="error">${escapeHtml(data.error || "Error")}</div>`;
        } else {
          showResult(data);
        }
      } catch (err) {
        if (requestId !== latestRequest) return;
        outputEl.innerHTML = `<div class="error">Error: ${escapeHtml(String(err))}</div>`;
      }
    }

    // --- Result ---

    function showResult(data) {
      currentHands = data.hands;
      activeLabel = null;
      outputEl.innerHTML =
        `<div class="filter-line">${escapeHtml(data.interpreted_filter)}</div>` +
        renderDistribution(data.distribution) +
        '<h3>Matching hands</h3><div id="hands"></div>';
      outputEl.querySelectorAll("table.dist tbody tr").forEach(row => {
        row.addEventListener("click", () => toggleLabel(row.dataset.label));
      });
      renderHands();
    }

    function toggleLabel(label) {
      activeLabel = activeLabel === label ? null : label;
      outputEl.querySelectorAll("table.dist tbody tr").forEach(row => {
        row.classList.toggle("selected", row.dataset.label === activeLabel);
      });
      renderHands();
    }

    function renderHands() {
      const rows = activeLabel ? currentHands.filter(hand => hand.measured_action === activeLabel) : currentHands;
      document.getElementById("hands").innerHTML = renderTable(rows);
    }

    function renderDistribution(distribution) {
      let html = '<table class="dist"><thead><tr><th>Action</th><th>Hands</th><th>%</th></tr></thead><tbody>';
      distribution.forEach(row => {
        html += `<tr data-label="${escapeHtml(row.label)}"><td>${escapeHtml(row.label)}</td>` +
          `<td>${row.hands.toLocaleString("en-US")}</td><td>${row.pct.toFixed(1)}%</td></tr>`;
      });
      html += "</tbody></table>";
      return html;
    }

    const CARD_COLUMNS = new Set(["hole_cards", "flop", "turn", "river"]);
    const WRAP_COLUMNS = new Set(["final_hand", "winning_hand"]);
    const SUIT_SYMBOLS = { c: "♣", d: "♦", h: "♥", s: "♠" };
    const RED_SUITS = new Set(["d", "h"]);

    const COLUMN_PRIORITY = [
      "date_played", "position", "measured_action", "final_hand", "hole_cards", "flop",
      "f_act", "amt_bet_f", "turn", "t_act", "amt_bet_t", "river", "r_act", "amt_bet_r",
      "winner", "winning_hand",
      "amt_pot", "amt_bb", "amt_won",
      "id_hand",
    ];

    function orderColumns(columns) {
      const known = COLUMN_PRIORITY.filter(col => columns.includes(col));
      const unknown = columns.filter(col => !COLUMN_PRIORITY.includes(col));
      return [...known, ...unknown];
    }

    function renderCards(cardStr) {
      if (!cardStr) return "—";
      return cardStr.trim().split(/\s+/).map(card => {
        const rank = card[0];
        const suit = card[1];
        const colorClass = RED_SUITS.has(suit) ? "card-red" : "card-black";
        return `<span class="card ${colorClass}">${escapeHtml(rank)}${SUIT_SYMBOLS[suit] || suit}</span>`;
      }).join(" ");
    }

    function formatCell(value) {
      if (value === null || value === undefined || value === "") return "—";
      if (typeof value === "number" && !Number.isInteger(value)) return value.toFixed(2);
      return escapeHtml(String(value));
    }

    function renderTable(rows) {
      if (!rows || rows.length === 0) return "<p>No matching hands.</p>";
      const columns = orderColumns(Object.keys(rows[0]));
      let html = '<div class="table-scroll"><table><thead><tr>';
      columns.forEach(col => html += `<th>${escapeHtml(col)}</th>`);
      html += "</tr></thead><tbody>";
      rows.forEach(row => {
        html += "<tr>";
        columns.forEach(col => {
          const cell = CARD_COLUMNS.has(col) ? renderCards(row[col]) : formatCell(row[col]);
          const cellClass = WRAP_COLUMNS.has(col) ? ' class="wrap"' : "";
          html += `<td${cellClass}>${cell}</td>`;
        });
        html += "</tr>";
      });
      html += "</tbody></table></div>";
      return html;
    }

    refreshPresets();
  </script>
</body>
</html>
```

- [ ] **Step 4: Run the config test, then the suite**

Run: `venv\Scripts\python -m pytest tests/test_static_config.py -v` → 2 PASS.
Sabotage check: temporarily swap `"BB vs CO"` and `"BB vs BTN"` in the JSON, rerun → `test_formations_match_the_backend` FAILS on the list diff; restore. Then `venv\Scripts\python -m pytest` → all PASS.

- [ ] **Step 5: Manual browser check**

Start: `venv\Scripts\python -m uvicorn api:app --port 8000`, open http://localhost:8000. Numbers below are from the live DB on 2026-10-13; if new hands were imported since, they grow but the checks' logic holds.

1. Page loads with 2BP / OOP / PFC on, LIMP and 4BP greyed and unclickable, Formations shows `Any`, Run disabled.
2. Focus the Line input: suggestions are `vs B?`, `vs B-X-?`, `vs X-C-?`. Click PFR: suggestions become `- B-?`, `- X-B-?`. Click PFC again.
3. Type `vs B?`, press plain `Enter` → nothing runs. Press `Ctrl+Enter` → filter line `2BP · OOP · PFC · Any · Flop: Hero X, villain B, measuring XF / XC / XR · 4,229 hands`; distribution `XF 1,843 43.6%`, `XC 1,990 47.1%`, `XR 396 9.4%`; hands table has a `measured_action` column right after `position`.
4. Click the `XC` row → it highlights, the hands table shows only `XC` rows (1,990). Click it again → highlight gone, all 4,229 rows back.
5. Click `XF` (filter on), then press Run → no row highlighted, all hands shown.
6. Open Formations, tick `BB vs BTN` and `BB vs CO`; the summary reads `BB vs BTN, BB vs CO`; click outside → panel closes. Run → `2,668 hands`, `XF 1,147`, `XC 1,262`, `XR 259`.
7. Click PFR (Line still `vs B?`), Run → under the input: `With PFR the Line starts with '-' (your letters)`; output cleared; the Line is still `vs B?`.
8. Back to PFC, set the Line to `vs B-` and Run → under the input: `Missing '?': mark where Hero's decision is measured`.
9. With the Line `vs B?`, press `Ctrl+Enter` twice quickly, then switch Formations to none and Run once more → the page ends showing the `Any` result (4,229), never a stale one.
10. Clear the Line → Run is disabled and `Ctrl+Enter` does nothing.

Any check that fails: fix before committing, and say which check failed and why in the commit message.

- [ ] **Step 6: Update `CLAUDE.md`**

In "Project scope", replace the last sentence of the second paragraph (`The code today is the earlier NL pipeline (LLM router behind \`POST /query\`), now **frozen** — kept working, not extended.`) with:

```markdown
`static/index.html` is the Spotlight page (vanilla JS, one file); the earlier NL pipeline (LLM router behind `POST /query`) is **frozen** — kept working, not extended, with no page of its own.
```

In the NL data-flow paragraph, replace `` `static/index.html` is the single-file vanilla-JS frontend served by `api.py`. `` with:

```markdown
`static/index.html` is the Spotlight page served by `api.py`; its Line presets and formation list live in a `<script id="spot-config">` JSON block that `tests/test_static_config.py` checks against `spot_sql.FORMATIONS` and `parse_line`.
```

- [ ] **Step 7: Commit**

```powershell
git add static/index.html tests/test_static_config.py CLAUDE.md
git commit -m "Spotlight page: bar, typed Line with presets, multi-select formations, row filter"
```

---

### Task 5: `pt4_diff.py` and the M5 validation

**Files:**
- Create: `pt4_diff.py`
- Test: `tests/test_pt4_diff.py`

**Interfaces:**
- Consumes: `run_spot(...)` (Task 2), `db.engine`.
- Produces: CLI `venv\Scripts\python pt4_diff.py <export.csv> <pot> <position> <role> "<line>" [--formation "BB vs BTN" ...] [--column "Hand #"]`, printing the interpreted filter and `Spotlight N · PT4 M · extra E · missing K` plus up to 20 hand numbers per side. Pure helpers `normalize_hand_no(value) -> str` and `diff_hand_sets(spot: set, export: set) -> {"extra": set, "missing": set}`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_pt4_diff.py`:

```python
import pytest
from pt4_diff import diff_hand_sets, normalize_hand_no


@pytest.mark.parametrize("raw, expected", [
    ("257244123456", "257244123456"),
    (" 257244123456 ", "257244123456"),
    ("257244123456.0", "257244123456"),
    (257244123456, "257244123456"),
])
def test_normalize_hand_no(raw, expected):
    assert normalize_hand_no(raw) == expected


def test_scientific_notation_is_rejected():
    with pytest.raises(ValueError, match="scientific notation"):
        normalize_hand_no("2.57244E+11")


def test_diff_is_both_directions():
    assert diff_hand_sets({"1", "2", "3"}, {"2", "3", "4"}) == {"extra": {"1"}, "missing": {"4"}}
```

- [ ] **Step 2: Run to verify they fail**

Run: `venv\Scripts\python -m pytest tests/test_pt4_diff.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pt4_diff'`.

- [ ] **Step 3: Implement**

Create `pt4_diff.py`:

```python
"""Diff a Spotlight result against a PT4 hand-list export by hand_no, both directions."""
import argparse

import pandas as pd

from db import engine
from spotlight import run_spot


def normalize_hand_no(value):
    text = str(value).strip()
    if "E" in text.upper():
        raise ValueError(f"hand_no {text!r} is in scientific notation; re-export with full numbers")
    return text[:-2] if text.endswith(".0") else text


def diff_hand_sets(spot, export):
    return {"extra": spot - export, "missing": export - spot}


def export_hand_nos(csv_path, column):
    df = pd.read_csv(csv_path, dtype=str)
    return {normalize_hand_no(v) for v in df[column].dropna()}


def spot_hand_nos(id_hands):
    if not id_hands:
        return set()
    df = pd.read_sql(
        "SELECT hand_no FROM cash_hand_summary WHERE id_hand = ANY(%(ids)s)",
        engine,
        params={"ids": id_hands},
    )
    return {normalize_hand_no(v) for v in df["hand_no"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv")
    parser.add_argument("pot")
    parser.add_argument("position")
    parser.add_argument("role")
    parser.add_argument("line")
    parser.add_argument("--formation", action="append", default=[])
    parser.add_argument("--column", default="Hand #")
    args = parser.parse_args()

    result = run_spot(args.pot, args.position, args.role, args.line, args.formation)
    hands = result["hands"]
    spot = spot_hand_nos([] if hands.empty else [int(i) for i in hands["id_hand"]])
    export = export_hand_nos(args.csv, args.column)
    diff = diff_hand_sets(spot, export)

    print(result["interpreted_filter"])
    print(f"Spotlight {len(spot)} · PT4 {len(export)} · extra {len(diff['extra'])} · missing {len(diff['missing'])}")
    for side in ("extra", "missing"):
        if diff[side]:
            print(f"{side}: {sorted(diff[side])[:20]}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run to verify they pass**

Run: `venv\Scripts\python -m pytest tests/test_pt4_diff.py -v` → all PASS. Then `venv\Scripts\python -m pytest` → all PASS.

- [ ] **Step 5: Commit**

```powershell
git add pt4_diff.py tests/test_pt4_diff.py
git commit -m "pt4_diff: hand_no set diff of a Spotlight result vs a PT4 export"
```

- [ ] **Step 6: M5 validation (needs the user)**

The user builds each spot as a filter in PT4 and exports the hand list as CSV (full hand numbers, not scientific notation) anywhere in the repo (`*.csv` is gitignored). For each, run the diff:

| # | Spot | Command |
|---|---|---|
| 1 | 2bp ip pfr `- B-B-?` | `venv\Scripts\python pt4_diff.py <csv> 2bp ip pfr "- B-B-?"` |
| 2 | 3bp oop pfr `- B-B-?` | `venv\Scripts\python pt4_diff.py <csv> 3bp oop pfr "- B-B-?"` |
| 3 | 2bp oop pfc `vs B-X-?` (1,006 on 2026-10-11) | `venv\Scripts\python pt4_diff.py <csv> 2bp oop pfc "vs B-X-?"` |
| 4 | 2bp oop pfc `vs B?` + `BB vs BTN` (1,639) | `venv\Scripts\python pt4_diff.py <csv> 2bp oop pfc "vs B?" --formation "BB vs BTN"` |

If the CSV's hand-number column isn't `Hand #`, pass `--column "<header>"`.

Pass = `extra 0 · missing 0` on all four. A non-zero diff is investigated hand by hand (superpowers:systematic-debugging), never "fixed in the test". If Spotlight turns out to be right, the reason goes in `docs/SCHEMA_NOTES.md`.

- [ ] **Step 7: The user's three failed questions, in the UI**

In the browser, each returns hands and a distribution:
- 2BP · IP · PFR, Line `- B-B-?`
- 3BP · IP · PFC, Line `vs B?`
- 3BP · OOP · PFR, Line `- B-B-?`

M5 closes when Steps 6 and 7 pass. Record the results in `docs/STATE.md` at wrap-up, and mark M5 ✅ in `docs/SPEC.md`'s ladder.
