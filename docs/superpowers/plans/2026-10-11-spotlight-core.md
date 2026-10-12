# Spotlight Core (M4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `POST /spot` turns `{pot, position, role, line, formation}` into
`{interpreted_filter, distribution, hands}`, matching the 9 validated recipes by exact hand set.

**Architecture:** A pure parser (`line_parser.py`) simulates each heads-up street from the
preflop raiser's letters and produces a `LineSpec` with exact Hero/villain PT4 action strings.
`spot_sql.py` compiles that plus the validated preflop-context atoms into a parameter-bound
WHERE clause. `db.run_spot_query()` executes it with the villain row and six `lookup_actions`
joins. `spotlight.py` orchestrates, and `api.py` exposes it.

**Tech Stack:** Python 3, FastAPI, pandas, SQLAlchemy/psycopg2 on PT4 Postgres, pytest.

**Spec:** `docs/superpowers/specs/2026-10-11-spotlight-design.md`

## Global Constraints

- All SQL values go through parameter binding (`%(name)s` + `params`); only fixed identifiers (street letters `f`/`t`/`r` from the parser's own tuple) are ever formatted into SQL.
- Hero is `id_player = 10` (same default as `run_filter_query`; id 9580 has 0 hands), so the oracle compares like with like.
- Strict TDD for every behavior: write the test, create a **stub** so the test runs, watch it fail with an `AssertionError` (an `ImportError` is not a valid RED), then implement.
- Inline comments: one line max, only for a non-obvious invariant. Provenance goes to `docs/SCHEMA_NOTES.md` / `docs/DECISIONS.md`.
- Default `pytest` run never touches Postgres. DB tests carry `@pytest.mark.db` and run with `pytest -m db`.
- Validation is exact hand-set membership in both directions, never a count match.
- Run Python through the venv: `venv\Scripts\python -m pytest ...`.

## Review Focus

- A Line with lowercase letters and stray spaces (`" -  b - ? "`) must behave exactly like `- B-?`. Pinned in Task 2.
- A spot with 0 matching hands must return 200 with an empty distribution, not crash in `get_hand_details` on an empty array. Pinned in Task 5.
- NaN cells in hand details must reach the JSON as `null`, not cause a 500 (the known `/query` bug). Pinned in Task 5.
- A misspelled formation (`"BTN vs BB"`, IP seat first) must be a 400 with a clear message, not silently ignored. Pinned in Task 3 and Task 6.
- Hands with no next Hero action at the decision (e.g. after `B?` the villain only called) must be excluded, not counted as an empty-string action. Pinned in Task 3 (SQL) and Task 7 (oracle).

---

### Task 1: `line_parser.py`, input validation

**Files:**
- Create: `line_parser.py`
- Test: `tests/test_line_parser.py`

**Interfaces:**
- Produces: `SpotInputError(ValueError)`; `parse_line(line: str, role: str, position: str) -> LineSpec`. In this task, `parse_line` only validates and raises; Task 2 makes it return.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_line_parser.py
import pytest
from line_parser import parse_line, SpotInputError


@pytest.mark.parametrize("line, role, position, message", [
    ("", "pfr", "ip", "Line is empty"),
    ("   ", "pfr", "ip", "Line is empty"),
    ("vs B?", "pfr", "ip", "With PFR the Line starts with '-'"),
    ("B-?", "pfr", "ip", "With PFR the Line starts with '-'"),
    ("- B?", "pfc", "ip", "With PFC the Line starts with 'vs'"),
    ("B?", "pfc", "oop", "With PFC the Line starts with 'vs'"),
    ("- B-", "pfr", "ip", "Missing '\\?'"),
    ("- ?-B", "pfr", "ip", "'\\?' must appear once, at the end"),
    ("- B?-?", "pfr", "ip", "'\\?' must appear once, at the end"),
    ("- B-B-B-?", "pfr", "oop", "at most 3 streets"),
    ("- -?", "pfr", "oop", "flop: empty street"),
    ("- D?", "pfr", "oop", "flop: unknown letter 'D'"),
    ("vs B-Z?", "pfc", "ip", "turn: unknown letter 'Z'"),
])
def test_invalid_line_raises_with_message(line, role, position, message):
    with pytest.raises(SpotInputError, match=message):
        parse_line(line, role, position)


@pytest.mark.parametrize("role, position, message", [
    ("caller", "ip", "Unknown role: caller"),
    ("pfr", "middle", "Unknown position: middle"),
])
def test_unknown_role_or_position_raises(role, position, message):
    with pytest.raises(SpotInputError, match=message):
        parse_line("- ?", role, position)


def test_spot_input_error_is_a_value_error():
    assert issubclass(SpotInputError, ValueError)
```

- [ ] **Step 2: Create the stub so the tests run**

```python
# line_parser.py
class SpotInputError(ValueError):
    pass


def parse_line(line, role, position):
    return None
```

- [ ] **Step 3: Run the tests and verify RED**

Run: `venv\Scripts\python -m pytest tests/test_line_parser.py -v`
Expected: the parametrized cases FAIL with `Failed: DID NOT RAISE`; `test_spot_input_error_is_a_value_error` PASSES.

- [ ] **Step 4: Implement validation**

```python
# line_parser.py
import re

STREETS = ("f", "t", "r")
STREET_NAMES = {"f": "flop", "t": "turn", "r": "river"}
LETTERS = set("XBCRF")


class SpotInputError(ValueError):
    pass


def _split_tokens(line, role, position):
    if role not in ("pfr", "pfc"):
        raise SpotInputError(f"Unknown role: {role}")
    if position not in ("ip", "oop"):
        raise SpotInputError(f"Unknown position: {position}")

    text = re.sub(r"\s+", "", line or "").upper()
    if not text:
        raise SpotInputError("Line is empty")

    if role == "pfr":
        if not text.startswith("-"):
            raise SpotInputError("With PFR the Line starts with '-' (your letters)")
        body = text[1:]
    else:
        if not text.startswith("VS"):
            raise SpotInputError("With PFC the Line starts with 'vs' (the villain's letters)")
        body = text[2:]

    if "?" not in body:
        raise SpotInputError("Missing '?': mark where Hero's decision is measured")
    if body.count("?") > 1 or not body.endswith("?"):
        raise SpotInputError("'?' must appear once, at the end of the Line")

    tokens = body[:-1].split("-")
    if len(tokens) > 3:
        raise SpotInputError("A Line has at most 3 streets (flop, turn, river)")

    for street, letters in zip(STREETS, tokens):
        name = STREET_NAMES[street]
        is_decision = street == STREETS[len(tokens) - 1]
        if not letters and not is_decision:
            raise SpotInputError(f"{name}: empty street")
        unknown = sorted(set(letters) - LETTERS)
        if unknown:
            raise SpotInputError(f"{name}: unknown letter '{unknown[0]}' (use X B C R F)")
    return tokens


def parse_line(line, role, position):
    _split_tokens(line, role, position)
    return None
```

Note: `body[:-1]` drops the final `?`, so `"B-?"` → tokens `["B", ""]`; the last token is the decision street's prefix (may be empty).

- [ ] **Step 5: Run the tests and verify GREEN**

Run: `venv\Scripts\python -m pytest tests/test_line_parser.py -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add line_parser.py tests/test_line_parser.py
git commit -m "Add line_parser input validation for Spotlight Lines"
```

---

### Task 2: `line_parser.py`, heads-up street resolution

**Files:**
- Modify: `line_parser.py`
- Test: `tests/test_line_parser.py`

**Interfaces:**
- Consumes: `_split_tokens`, `SpotInputError`, `STREETS`, `STREET_NAMES` from Task 1.
- Produces:
  - `StreetSpec(street: str, hero: str, villain: str)`, a frozen dataclass. `street` ∈ `"f"/"t"/"r"`. For completed streets `hero`/`villain` are full PT4 action strings; for the decision street they are the prefixes before Hero's measured action.
  - `LineSpec(completed: tuple[StreetSpec, ...], decision: StreetSpec, measured: tuple[str, ...])`, a frozen dataclass. `measured` is `("B", "X")` or `("F", "C", "R")`.
  - `parse_line(line, role, position) -> LineSpec`.

Model: heads-up, seat 0 = OOP acts first on every street. Not facing a bet → `X`/`B`; facing → `F`/`C`/`R`. A street closes on `C` or on a second consecutive `X`. The PFR's letters must match exactly one sequence; the other player's string is read off it.

- [ ] **Step 1: Write the failing tests (the 20 v1 Lines + extra cases + errors)**

Append to `tests/test_line_parser.py`:

```python
from line_parser import StreetSpec, LineSpec

BX = ("B", "X")
FCR = ("F", "C", "R")


def S(street, hero, villain):
    return StreetSpec(street, hero, villain)


@pytest.mark.parametrize("line, role, position, expected", [
    # Pre-river
    ("vs B?", "pfc", "ip", LineSpec((), S("f", "", "B"), FCR)),                      # P1, P9
    ("vs B?", "pfc", "oop", LineSpec((), S("f", "X", "B"), FCR)),                    # P2, P8
    ("- B-?", "pfr", "ip", LineSpec((S("f", "B", "XC"),), S("t", "", "X"), BX)),     # P3, P7
    ("- B-?", "pfr", "oop", LineSpec((S("f", "B", "C"),), S("t", "", ""), BX)),      # P4, P5
    ("vs B-B?", "pfc", "ip", LineSpec((S("f", "C", "B"),), S("t", "", "B"), FCR)),   # P6
    ("vs X?", "pfc", "ip", LineSpec((), S("f", "", "X"), BX)),                       # P10
    # River
    ("- B-B-?", "pfr", "oop",
     LineSpec((S("f", "B", "C"), S("t", "B", "C")), S("r", "", ""), BX)),            # R1
    ("- B-B-?", "pfr", "ip",
     LineSpec((S("f", "B", "XC"), S("t", "B", "XC")), S("r", "", "X"), BX)),         # R2, R7
    ("- B-X-?", "pfr", "oop",
     LineSpec((S("f", "B", "C"), S("t", "X", "X")), S("r", "", ""), BX)),            # R3
    ("vs B-X-?", "pfc", "oop",
     LineSpec((S("f", "XC", "B"), S("t", "X", "X")), S("r", "", ""), BX)),           # R4, R8
    ("vs X-C-?", "pfc", "oop",
     LineSpec((S("f", "X", "X"), S("t", "B", "C")), S("r", "", ""), BX)),            # R5
    ("- X-B-?", "pfr", "oop",
     LineSpec((S("f", "X", "X"), S("t", "B", "C")), S("r", "", ""), BX)),            # R6
    ("- X-B-?", "pfr", "ip",
     LineSpec((S("f", "X", "X"), S("t", "B", "XC")), S("r", "", "X"), BX)),          # R9
    ("vs B-XC-X?", "pfc", "ip",
     LineSpec((S("f", "C", "B"), S("t", "B", "XC")), S("r", "", "X"), BX)),          # R10
    # Decisions after Hero already acted on the street
    ("- B-B?", "pfr", "oop", LineSpec((S("f", "B", "C"),), S("t", "B", "R"), FCR)),
    ("- B-B?", "pfr", "ip", LineSpec((S("f", "B", "XC"),), S("t", "B", "XR"), FCR)),
    ("- X?", "pfr", "oop", LineSpec((), S("f", "X", "B"), FCR)),
    ("- ?", "pfr", "oop", LineSpec((), S("f", "", ""), BX)),
])
def test_valid_line_resolves(line, role, position, expected):
    assert parse_line(line, role, position) == expected


def test_case_and_whitespace_are_ignored():
    assert parse_line(" -  b - ? ", "pfr", "ip") == parse_line("- B-?", "pfr", "ip")


@pytest.mark.parametrize("line, role, position, message", [
    ("- XX-?", "pfr", "oop", "flop: 'XX' is impossible heads-up"),
    ("- BB-?", "pfr", "oop", "flop: 'BB' is impossible heads-up"),
    ("- X?", "pfr", "ip", "flop: 'X' is impossible heads-up"),
    ("- F-?", "pfr", "oop", "flop: 'F' is impossible heads-up"),
    ("vs B-?", "pfc", "ip", "Hero is IP: the villain acts first on the turn"),
    ("vs ?", "pfc", "ip", "Hero is IP: the villain acts first on the flop"),
])
def test_impossible_sequences_raise(line, role, position, message):
    with pytest.raises(SpotInputError, match=message):
        parse_line(line, role, position)
```

- [ ] **Step 2: Add the dataclasses and keep `parse_line` returning `None`**

Add to `line_parser.py` (above `parse_line`), leaving `parse_line` as is:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class StreetSpec:
    street: str
    hero: str
    villain: str


@dataclass(frozen=True)
class LineSpec:
    completed: tuple
    decision: StreetSpec
    measured: tuple
```

- [ ] **Step 3: Run the tests and verify RED**

Run: `venv\Scripts\python -m pytest tests/test_line_parser.py -v`
Expected: `test_valid_line_resolves` cases FAIL with `assert None == LineSpec(...)`; `test_impossible_sequences_raise` cases FAIL with `DID NOT RAISE`; Task 1 tests still PASS.

- [ ] **Step 4: Implement street resolution**

Add to `line_parser.py` and replace `parse_line`:

```python
MAX_ACTIONS = 8


def _all_sequences():
    """Every heads-up street sequence as (actions, closed); seat 0 (OOP) acts first."""
    found = []

    def walk(seq, facing, checks):
        found.append((tuple(seq), False))
        if len(seq) >= MAX_ACTIONS:
            return
        for action in (("F", "C", "R") if facing else ("X", "B")):
            if action == "F":
                continue  # a fold ends the hand, so it is never part of a Line
            nxt = seq + [action]
            if action == "C" or (action == "X" and checks == 1):
                found.append((tuple(nxt), True))
            else:
                walk(nxt, action in "BR", checks + (action == "X"))

    walk([], False, 0)
    return found


SEQUENCES = _all_sequences()


def _seat_strings(seq):
    return "".join(seq[0::2]), "".join(seq[1::2])


def _is_facing(seq):
    return bool(seq) and seq[-1] in "BR"


def _resolve(street, letters, is_decision, hero_seat, pfr_seat, role):
    matches = []
    for seq, closed in SEQUENCES:
        if closed == is_decision:
            continue
        if _seat_strings(seq)[pfr_seat] != letters:
            continue
        if is_decision and len(seq) % 2 != hero_seat:
            continue
        matches.append(seq)
    if is_decision and role == "pfr" and letters == "":
        matches = [seq for seq in matches if not _is_facing(seq)]  # no donks in v1
    if len(matches) != 1:
        problem = "is impossible" if not matches else "is ambiguous"
        raise SpotInputError(f"{STREET_NAMES[street]}: '{letters}' {problem} heads-up")
    return matches[0]


def parse_line(line, role, position):
    tokens = _split_tokens(line, role, position)
    hero_seat = 0 if position == "oop" else 1
    pfr_seat = hero_seat if role == "pfr" else 1 - hero_seat

    decision_street = STREETS[len(tokens) - 1]
    if role == "pfc" and hero_seat == 1 and tokens[-1] == "":
        raise SpotInputError(
            f"Hero is IP: the villain acts first on the {STREET_NAMES[decision_street]}; "
            "write his action before '?'"
        )

    completed = []
    for street, letters in zip(STREETS, tokens):
        is_decision = street == decision_street
        seq = _resolve(street, letters, is_decision, hero_seat, pfr_seat, role)
        strings = _seat_strings(seq)
        spec = StreetSpec(street, strings[hero_seat], strings[1 - hero_seat])
        if is_decision:
            measured = ("F", "C", "R") if _is_facing(seq) else ("B", "X")
            return LineSpec(tuple(completed), spec, measured)
        completed.append(spec)
```

- [ ] **Step 5: Run the tests and verify GREEN**

Run: `venv\Scripts\python -m pytest tests/test_line_parser.py -v`
Expected: all PASS. If an expected `LineSpec` in the table disagrees with the implementation, stop and reason through the street by hand. The table was derived by hand from the poker rules, and either side can be wrong. Don't edit the expectation just to go green.

- [ ] **Step 6: Commit**

```bash
git add line_parser.py tests/test_line_parser.py
git commit -m "Resolve Spotlight Lines into heads-up Hero/villain action strings"
```

---

### Task 3: `spot_sql.py`, compile a LineSpec to a WHERE clause

**Files:**
- Create: `spot_sql.py`
- Test: `tests/test_spot_sql.py`

**Interfaces:**
- Consumes: `LineSpec`, `StreetSpec`, `SpotInputError` from `line_parser`; `assemble_where(items) -> (where_sql, params)` from `filter_recipes`.
- Produces:
  - `PREFLOP_CONTEXTS: dict[(pot, role), list]`, `SEATS: dict[str, int]`, `FORMATIONS: list[str]`
  - `build_spot_query(pot, position, role, spec, formation=None) -> (where_sql: str, params: dict, measured_sql: str)`. `where_sql` starts with ` AND `. `measured_sql` is an SQL expression over alias `h_<street>`; Task 4's skeleton defines the aliases `chps`, `chs`, `v`, `h_f`, `h_t`, `h_r`, `v_f`, `v_t`, `v_r`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_spot_sql.py
import pytest
from line_parser import parse_line, SpotInputError
from spot_sql import build_spot_query, FORMATIONS, PREFLOP_CONTEXTS


def build(pot, position, role, line, formation=None):
    spec = parse_line(line, role, position)
    return build_spot_query(pot, position, role, spec, formation)


def test_completed_streets_bind_exact_strings():
    where, params, _ = build("2bp", "ip", "pfr", "- B-?")
    assert "h_f.action = %(h_f)s" in where
    assert "v_f.action = %(v_f)s" in where
    assert params["h_f"] == "B"
    assert params["v_f"] == "XC"


def test_decision_street_binds_prefixes_and_measured_set():
    where, params, measured_sql = build("2bp", "oop", "pfc", "vs B?")
    assert "h_f.action LIKE %(h_f_prefix)s" in where
    assert "v_f.action LIKE %(v_f_prefix)s" in where
    assert params["h_f_prefix"] == "X%"
    assert params["v_f_prefix"] == "B%"
    assert measured_sql == "substr(h_f.action, %(measure_pos)s, 1)"
    assert params["measure_pos"] == 2
    assert f"{measured_sql} = ANY(%(measured)s)" in where
    assert params["measured"] == ["F", "C", "R"]


def test_line_letters_never_reach_the_sql_text():
    where, _, _ = build("3bp", "ip", "pfc", "vs B-XC-X?")
    assert "'XC'" not in where and "'B'" not in where


def test_preflop_context_and_position_are_applied():
    where, params, _ = build("3bp", "oop", "pfr", "- B-?")
    assert "chps.flg_p_3bet = true" in where
    assert "chps.flg_f_has_position = false" in where
    assert "chs.cnt_players_f = 2" in where
    assert params["own_raises_2"] == 1  # assemble_where names it <atom>_<index>


def test_every_pot_role_pair_has_a_context():
    assert set(PREFLOP_CONTEXTS) == {("2bp", "pfr"), ("2bp", "pfc"), ("3bp", "pfr"), ("3bp", "pfc")}


def test_no_formation_adds_no_seat_condition():
    where, params, _ = build("2bp", "ip", "pfr", "- B-?")
    assert "chps.position" not in where
    assert "hero_pos" not in params


@pytest.mark.parametrize("position, hero_pos, villain_pos", [("oop", 8, 0), ("ip", 0, 8)])
def test_formation_maps_hero_seat_from_position(position, hero_pos, villain_pos):
    role, line = ("pfc", "vs B?") if position == "oop" else ("pfr", "- B-?")
    where, params, _ = build("2bp", position, role, line, "BB vs BTN")
    assert "chps.position = %(hero_pos)s AND v.position = %(villain_pos)s" in where
    assert (params["hero_pos"], params["villain_pos"]) == (hero_pos, villain_pos)


def test_formations_are_oop_first_and_complete():
    assert len(FORMATIONS) == 15
    assert "BB vs BTN" in FORMATIONS and "SB vs BB" in FORMATIONS
    assert "BTN vs BB" not in FORMATIONS


@pytest.mark.parametrize("pot, formation, message", [
    ("4bp", None, "Unknown pot: 4bp"),
    ("2bp", "BTN vs BB", "Unknown formation: BTN vs BB"),
])
def test_bad_bar_values_raise(pot, formation, message):
    spec = parse_line("- B-?", "pfr", "ip")
    with pytest.raises(SpotInputError, match=message):
        build_spot_query(pot, "ip", "pfr", spec, formation)
```

- [ ] **Step 2: Create the stub**

```python
# spot_sql.py
PREFLOP_CONTEXTS = {}
FORMATIONS = []


def build_spot_query(pot, position, role, spec, formation=None):
    return "", {}, ""
```

- [ ] **Step 3: Run the tests and verify RED**

Run: `venv\Scripts\python -m pytest tests/test_spot_sql.py -v`
Expected: FAIL with `AssertionError` / `KeyError` on the asserts. `test_line_letters_never_reach_the_sql_text` and `test_no_formation_adds_no_seat_condition` may pass vacuously against the stub; that's acceptable since they guard against regressions, not new behavior.

- [ ] **Step 4: Implement**

```python
# spot_sql.py
from filter_recipes import assemble_where
from line_parser import SpotInputError

# Preflop part of the validated recipes (SCHEMA_NOTES.md); position is added separately.
PREFLOP_CONTEXTS = {
    ("2bp", "pfr"): ["first_raise", "no_limpers_faced", "no_face_raise_preflop"],
    ("3bp", "pfr"): [
        "made_3bet", "had_3bet_opp", ("own_raises", "=", 1), "faced_raise_preflop",
        "no_4bet_faced", "no_squeeze_made",
    ],
    ("2bp", "pfc"): [
        "vpip", "no_first_raise", "no_3bet_made", ("own_raises", "=", 0),
        "faced_raise_preflop", "no_fold_preflop", "no_3bet_def_faced",
    ],
    ("3bp", "pfc"): [
        ("own_raises", "<=", 1), "faced_3bet_preflop", "no_4bet_made", "no_4bet_faced",
        "no_fold_preflop", "no_squeeze_def_faced", "first_raise", "no_limpers_faced",
    ],
}
POSITION_ATOMS = {"ip": "ip_flop", "oop": "oop_flop"}

SEATS = {"SB": 9, "BB": 8, "UTG": 3, "MP": 2, "CO": 1, "BTN": 0}
POSTFLOP_ORDER = ["SB", "BB", "UTG", "MP", "CO", "BTN"]
FORMATIONS = [
    f"{oop} vs {ip}"
    for i, oop in enumerate(POSTFLOP_ORDER)
    for ip in POSTFLOP_ORDER[i + 1:]
]


def build_spot_query(pot, position, role, spec, formation=None):
    if pot not in ("2bp", "3bp"):
        raise SpotInputError(f"Unknown pot: {pot}")
    items = PREFLOP_CONTEXTS[(pot, role)] + ["heads_up_flop", POSITION_ATOMS[position]]
    where, params = assemble_where(items)

    for s in spec.completed:
        where += f" AND h_{s.street}.action = %(h_{s.street})s"
        where += f" AND v_{s.street}.action = %(v_{s.street})s"
        params[f"h_{s.street}"] = s.hero
        params[f"v_{s.street}"] = s.villain

    d = spec.decision
    measured_sql = f"substr(h_{d.street}.action, %(measure_pos)s, 1)"
    where += f" AND h_{d.street}.action LIKE %(h_{d.street}_prefix)s"
    where += f" AND v_{d.street}.action LIKE %(v_{d.street}_prefix)s"
    where += f" AND {measured_sql} = ANY(%(measured)s)"
    params[f"h_{d.street}_prefix"] = d.hero + "%"
    params[f"v_{d.street}_prefix"] = d.villain + "%"
    params["measure_pos"] = len(d.hero) + 1
    params["measured"] = list(spec.measured)

    if formation is not None:
        if formation not in FORMATIONS:
            raise SpotInputError(f"Unknown formation: {formation} (write the OOP seat first)")
        oop_seat, ip_seat = formation.split(" vs ")
        hero_seat, villain_seat = (oop_seat, ip_seat) if position == "oop" else (ip_seat, oop_seat)
        where += " AND chps.position = %(hero_pos)s AND v.position = %(villain_pos)s"
        params["hero_pos"] = SEATS[hero_seat]
        params["villain_pos"] = SEATS[villain_seat]

    return where, params, measured_sql
```

- [ ] **Step 5: Run the tests and verify GREEN**

Run: `venv\Scripts\python -m pytest tests/test_spot_sql.py tests/test_line_parser.py -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add spot_sql.py tests/test_spot_sql.py
git commit -m "Compile Spotlight LineSpecs into parameter-bound WHERE clauses"
```

---

### Task 4: `db.run_spot_query`

**Files:**
- Modify: `db.py` (add after `run_distribution_query`)
- Test: `tests/test_db.py`

**Interfaces:**
- Consumes: `(where_sql, params, measured_sql)` from Task 3.
- Produces: `run_spot_query(where_clause, params, measured_sql, id_player=10) -> DataFrame[id_hand, measured_action]`, ordered by `id_hand`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_db.py` (and add `run_spot_query` to its `from db import (...)`):

```python
def test_run_spot_query_builds_skeleton_and_binds_params(monkeypatch):
    monkeypatch.setattr("db.pd.read_sql", fake_read_sql)
    result = run_spot_query(" AND h_f.action = %(h_f)s", {"h_f": "B"},
                            "substr(h_t.action, %(measure_pos)s, 1)", id_player=42)
    query = result["query"]
    assert "substr(h_t.action, %(measure_pos)s, 1) AS measured_action" in query
    assert "v.id_player <> chps.id_player AND v.flg_f_saw = true" in query
    for alias in ("h_f", "h_t", "h_r", "v_f", "v_t", "v_r"):
        assert f"lookup_actions {alias} ON" in query
    assert query.rstrip().endswith("ORDER BY chps.id_hand")
    assert " AND h_f.action = %(h_f)s" in query
    assert result["params"] == {"h_f": "B", "id_player": 42}
```

- [ ] **Step 2: Create the stub**

Add to `db.py`:

```python
def run_spot_query(where_clause, params, measured_sql, id_player=10):
    return {"query": "", "params": {}}
```

- [ ] **Step 3: Run and verify RED**

Run: `venv\Scripts\python -m pytest tests/test_db.py -v`
Expected: `test_run_spot_query_builds_skeleton_and_binds_params` FAILS with `AssertionError`; other db tests PASS.

- [ ] **Step 4: Implement**

Replace the stub in `db.py`:

```python
def run_spot_query(where_clause, params, measured_sql, id_player=10):

    query = f"""
        SELECT chps.id_hand, {measured_sql} AS measured_action
        FROM cash_hand_player_statistics chps
            JOIN cash_hand_summary chs ON chps.id_hand = chs.id_hand
            JOIN cash_hand_player_statistics v
                ON v.id_hand = chps.id_hand AND v.id_player <> chps.id_player AND v.flg_f_saw = true
            JOIN lookup_actions h_f ON chps.id_action_f = h_f.id_action
            JOIN lookup_actions h_t ON chps.id_action_t = h_t.id_action
            JOIN lookup_actions h_r ON chps.id_action_r = h_r.id_action
            JOIN lookup_actions v_f ON v.id_action_f = v_f.id_action
            JOIN lookup_actions v_t ON v.id_action_t = v_t.id_action
            JOIN lookup_actions v_r ON v.id_action_r = v_r.id_action
        WHERE chps.id_player = %(id_player)s
            """ + where_clause + """
        ORDER BY chps.id_hand"""

    params = params | {"id_player": id_player}
    return pd.read_sql(query, engine, params=params)
```

(`lookup_actions` has `id_action = 0` → `''`, so the inner joins keep players who didn't act on a street.)

- [ ] **Step 5: Run and verify GREEN**

Run: `venv\Scripts\python -m pytest tests/test_db.py -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add db.py tests/test_db.py
git commit -m "Add run_spot_query: Hero + villain action-string joins"
```

---

### Task 5: `spotlight.py`, orchestration, distribution, interpreted filter

**Files:**
- Create: `spotlight.py`
- Test: `tests/test_spotlight.py`

**Interfaces:**
- Consumes: `parse_line` (Task 2), `build_spot_query` (Task 3), `run_spot_query` (Task 4), `db.get_hand_details(id_hands, id_player=10)` (existing).
- Produces:
  - `run_spot(pot, position, role, line, formation=None) -> {"interpreted_filter": str, "distribution": list[dict], "hands": DataFrame}`. Distribution rows are `{"action": "B", "name": "Bet", "hands": int, "pct": float}` in the measured-set order, including zero rows. `hands` carries a `measured_action` column, with NaN replaced by `None`.
  - `describe(pot, position, role, formation, spec, n_hands) -> str`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_spotlight.py
import numpy as np
import pandas as pd
from line_parser import parse_line
import spotlight


def fake_matches(rows):
    return pd.DataFrame(rows, columns=["id_hand", "measured_action"])


def install(monkeypatch, matches, details=None):
    monkeypatch.setattr("spotlight.run_spot_query", lambda where, params, measured_sql: matches)
    calls = []

    def fake_details(id_hands):
        calls.append(list(id_hands))
        return details if details is not None else pd.DataFrame({"id_hand": list(id_hands)})

    monkeypatch.setattr("spotlight.get_hand_details", fake_details)
    return calls


def test_distribution_counts_in_measured_order_with_zero_rows(monkeypatch):
    install(monkeypatch, fake_matches([(1, "C"), (2, "C"), (3, "F")]))
    result = spotlight.run_spot("2bp", "oop", "pfc", "vs B?")
    assert result["distribution"] == [
        {"action": "F", "name": "Fold", "hands": 1, "pct": 33.3},
        {"action": "C", "name": "Call", "hands": 2, "pct": 66.7},
        {"action": "R", "name": "Raise", "hands": 0, "pct": 0.0},
    ]


def test_hands_carry_measured_action(monkeypatch):
    install(monkeypatch, fake_matches([(7, "B"), (8, "X")]))
    hands = spotlight.run_spot("2bp", "ip", "pfr", "- B-?")["hands"]
    assert dict(zip(hands["id_hand"], hands["measured_action"])) == {7: "B", 8: "X"}


def test_zero_hands_skips_detail_query_and_returns_empty(monkeypatch):
    calls = install(monkeypatch, fake_matches([]))
    result = spotlight.run_spot("2bp", "ip", "pfr", "- B-?")
    assert calls == []
    assert result["hands"].empty
    assert [row["hands"] for row in result["distribution"]] == [0, 0]
    assert result["interpreted_filter"].endswith("0 hands")


def test_nan_in_hand_details_becomes_none(monkeypatch):
    details = pd.DataFrame({"id_hand": [1], "amt_won": [np.nan]})
    install(monkeypatch, fake_matches([(1, "B")]), details)
    hands = spotlight.run_spot("2bp", "ip", "pfr", "- B-?")["hands"]
    assert hands.to_dict(orient="records") == [{"id_hand": 1, "amt_won": None, "measured_action": "B"}]


def test_describe_reads_like_the_bar():
    spec = parse_line("- B-?", "pfr", "ip")
    text = spotlight.describe("2bp", "ip", "pfr", "BB vs BTN", spec, 1204)
    assert text == "2BP · IP · PFR · BB vs BTN · Flop: Hero B, villain XC · Turn: villain X, measuring B / X · 1,204 hands"


def test_describe_without_formation_says_any():
    spec = parse_line("vs B?", "pfc", "oop")
    text = spotlight.describe("3bp", "oop", "pfc", None, spec, 5)
    assert text == "3BP · OOP · PFC · Any · Flop: Hero X, villain B, measuring F / C / R · 5 hands"
```

- [ ] **Step 2: Create the stub**

```python
# spotlight.py
from db import run_spot_query, get_hand_details


def describe(pot, position, role, formation, spec, n_hands):
    return ""


def run_spot(pot, position, role, line, formation=None):
    return {"interpreted_filter": "", "distribution": [], "hands": None}
```

- [ ] **Step 3: Run and verify RED**

Run: `venv\Scripts\python -m pytest tests/test_spotlight.py -v`
Expected: every test FAILS with `AssertionError` or `TypeError: 'NoneType' object is not subscriptable`. A `TypeError` on the stub's `None` still means the assert line ran its target; if you want a pure `AssertionError`, return `pd.DataFrame()` for `hands` in the stub.

- [ ] **Step 4: Implement**

```python
# spotlight.py
import pandas as pd

from db import run_spot_query, get_hand_details
from line_parser import parse_line, STREET_NAMES
from spot_sql import build_spot_query

ACTION_NAMES = {"B": "Bet", "X": "Check", "F": "Fold", "C": "Call", "R": "Raise"}


def describe(pot, position, role, formation, spec, n_hands):
    parts = [pot.upper(), position.upper(), role.upper(), formation or "Any"]
    for s in spec.completed:
        parts.append(f"{STREET_NAMES[s.street].capitalize()}: Hero {s.hero}, villain {s.villain}")
    d = spec.decision
    seen = [f"Hero {d.hero}"] * bool(d.hero) + [f"villain {d.villain}"] * bool(d.villain)
    measuring = "measuring " + " / ".join(spec.measured)
    parts.append(f"{STREET_NAMES[d.street].capitalize()}: " + ", ".join(seen + [measuring]))
    parts.append(f"{n_hands:,} hands")
    return " · ".join(parts)


def _distribution(measured_actions, measured):
    counts = measured_actions.value_counts()
    total = int(counts.sum())
    return [
        {
            "action": action,
            "name": ACTION_NAMES[action],
            "hands": int(counts.get(action, 0)),
            "pct": round(counts.get(action, 0) / total * 100, 1) if total else 0.0,
        }
        for action in measured
    ]


def run_spot(pot, position, role, line, formation=None):
    spec = parse_line(line, role, position)
    where, params, measured_sql = build_spot_query(pot, position, role, spec, formation)
    matches = run_spot_query(where, params, measured_sql)

    if matches.empty:
        hands = pd.DataFrame()  # ANY('{}') on an untyped empty array fails in Postgres
    else:
        hands = get_hand_details(matches["id_hand"]).merge(matches, on="id_hand", how="left")
        hands = hands.astype(object).where(hands.notna(), None)

    return {
        "interpreted_filter": describe(pot, position, role, formation, spec, len(matches)),
        "distribution": _distribution(matches["measured_action"], spec.measured),
        "hands": hands,
    }
```

- [ ] **Step 5: Run and verify GREEN**

Run: `venv\Scripts\python -m pytest tests/test_spotlight.py -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add spotlight.py tests/test_spotlight.py
git commit -m "Add spotlight.run_spot: distribution, hand details, interpreted filter"
```

---

### Task 6: `POST /spot`

**Files:**
- Modify: `api.py` (new request model + endpoint, above the `app.mount` line)
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `spotlight.run_spot` (Task 5), `SpotInputError` (Task 1).
- Produces: `POST /spot` → 200 `{"interpreted_filter", "distribution", "hands": [records]}` or 400 `{"error": str}`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_api.py`:

```python
from line_parser import SpotInputError

SPOT_BODY = {"pot": "2bp", "position": "ip", "role": "pfr", "line": "- B-?", "formation": None}


def test_spot_returns_result_shape(monkeypatch):
    fake = {
        "interpreted_filter": "2BP · IP · PFR · Any · ...",
        "distribution": [{"action": "B", "name": "Bet", "hands": 1, "pct": 100.0}],
        "hands": pd.DataFrame({"id_hand": [1], "measured_action": ["B"]}),
    }
    calls = []

    def fake_run_spot(pot, position, role, line, formation=None):
        calls.append((pot, position, role, line, formation))
        return fake

    monkeypatch.setattr("api.run_spot", fake_run_spot)
    response = client.post("/spot", json=SPOT_BODY)
    assert response.status_code == 200
    assert response.json() == {
        "interpreted_filter": "2BP · IP · PFR · Any · ...",
        "distribution": [{"action": "B", "name": "Bet", "hands": 1, "pct": 100.0}],
        "hands": [{"id_hand": 1, "measured_action": "B"}],
    }
    assert calls == [("2bp", "ip", "pfr", "- B-?", None)]


def test_spot_input_error_is_400_with_message(monkeypatch):
    def fake_run_spot(*args, **kwargs):
        raise SpotInputError("Unknown formation: BTN vs BB (write the OOP seat first)")

    monkeypatch.setattr("api.run_spot", fake_run_spot)
    response = client.post("/spot", json=SPOT_BODY | {"formation": "BTN vs BB"})
    assert response.status_code == 400
    assert response.json() == {"error": "Unknown formation: BTN vs BB (write the OOP seat first)"}


def test_spot_real_parser_error_is_400():
    response = client.post("/spot", json=SPOT_BODY | {"line": "- B-"})
    assert response.status_code == 400
    assert "Missing '?'" in response.json()["error"]
```

- [ ] **Step 2: Create the stub**

Add to `api.py` (imports at top, endpoint above `app.mount`):

```python
from line_parser import SpotInputError
from spotlight import run_spot


class SpotRequest(BaseModel):
    pot: str
    position: str
    role: str
    line: str
    formation: str | None = None


@app.post("/spot")
def spot(request: SpotRequest):
    return {}
```

- [ ] **Step 3: Run and verify RED**

Run: `venv\Scripts\python -m pytest tests/test_api.py -v`
Expected: the three new tests FAIL with `AssertionError` (200 `{}` vs expected); existing `/query` tests PASS.

- [ ] **Step 4: Implement**

Replace the stub body:

```python
@app.post("/spot")
def spot(request: SpotRequest):
    try:
        result = run_spot(request.pot, request.position, request.role, request.line, request.formation)
    except SpotInputError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    return {
        "interpreted_filter": result["interpreted_filter"],
        "distribution": result["distribution"],
        "hands": result["hands"].to_dict(orient="records"),
    }
```

- [ ] **Step 5: Run and verify GREEN, then the full suite**

Run: `venv\Scripts\python -m pytest tests/test_api.py -v` → all PASS.
Run: `venv\Scripts\python -m pytest` → all PASS (no Postgres needed).

- [ ] **Step 6: Commit**

```bash
git add api.py tests/test_api.py
git commit -m "Expose Spotlight as POST /spot with 400 on bad input"
```

---

### Task 7: Oracle against the 9 validated recipes (real Postgres)

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/test_spotlight_oracle.py`
- Possibly modify: `docs/SCHEMA_NOTES.md` (only if a diff is investigated and justified)

**Interfaces:**
- Consumes: `build_where_clause`, `run_filter_query`, `compute_distribution`, `LINES` (existing); `parse_line`, `build_spot_query`, `run_spot_query` (Tasks 2–4).

- [ ] **Step 1: Register the `db` marker and exclude it by default**

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
addopts = "-v -m 'not db'"
markers = ["db: hits the real PT4 Postgres database (run with: pytest -m db)"]
```

Run: `venv\Scripts\python -m pytest` → same pass count as Task 6, nothing deselected yet.

- [ ] **Step 2: Write the oracle test**

```python
# tests/test_spotlight_oracle.py
import pytest
from analytics import compute_distribution
from db import run_filter_query, run_spot_query
from filter_recipes import build_where_clause
from line_parser import parse_line
from lines import LINES
from spot_sql import build_spot_query

pytestmark = pytest.mark.db

ORACLE = [
    ("2bp_ip_pfr_turn_cbet_opp", "2bp", "ip", "pfr", "- B-?"),
    ("2bp_oop_pfr_turn_cbet_opp", "2bp", "oop", "pfr", "- B-?"),
    ("3bp_ip_pfr_turn_cbet_opp", "3bp", "ip", "pfr", "- B-?"),
    ("3bp_oop_pfr_turn_cbet_opp", "3bp", "oop", "pfr", "- B-?"),
    ("2bp_ip_pfc_faced_cbet_flop", "2bp", "ip", "pfc", "vs B?"),
    ("2bp_oop_pfc_faced_cbet_flop", "2bp", "oop", "pfc", "vs B?"),
    ("3bp_ip_pfc_faced_cbet_flop", "3bp", "ip", "pfc", "vs B?"),
    ("3bp_oop_pfc_faced_cbet_flop", "3bp", "oop", "pfc", "vs B?"),
    ("3bp_ip_pfc_faced_barrel_turn", "3bp", "ip", "pfc", "vs B-B?"),
]
NAME_TO_LETTER = {"bet": "B", "check": "X", "raise": "R", "call": "C", "fold": "F"}
JUSTIFIED_EXCEPTIONS = {}  # recipe -> {"extra": set(), "missing": set()}, each documented in SCHEMA_NOTES.md


@pytest.mark.parametrize("recipe, pot, position, role, line", ORACLE)
def test_spotlight_matches_recipe(recipe, pot, position, role, line):
    where, params = build_where_clause(recipe)
    recipe_hands = set(run_filter_query(where, params)["id_hand"])

    spec = parse_line(line, role, position)
    s_where, s_params, measured_sql = build_spot_query(pot, position, role, spec)
    spot = run_spot_query(s_where, s_params, measured_sql)
    spot_hands = set(spot["id_hand"])

    allowed = JUSTIFIED_EXCEPTIONS.get(recipe, {"extra": set(), "missing": set()})
    extra = spot_hands - recipe_hands - allowed["extra"]
    missing = recipe_hands - spot_hands - allowed["missing"]
    assert not extra and not missing, (
        f"{recipe}: {len(extra)} extra {sorted(extra)[:10]}, {len(missing)} missing {sorted(missing)[:10]}"
    )

    if not allowed["extra"] and not allowed["missing"]:
        recipe_dist = compute_distribution(where, params, LINES[recipe])
        expected = {NAME_TO_LETTER[name]: v["count"] for name, v in recipe_dist.items() if v["count"]}
        assert spot["measured_action"].value_counts().to_dict() == expected
```

- [ ] **Step 3: Run it against Postgres**

Run: `venv\Scripts\python -m pytest -m db -v`
Expected: 9 PASS. Confirm `venv\Scripts\python -m pytest` still deselects these 9.

- [ ] **Step 4: If any case fails, investigate. Do not edit the test to pass.**

For each failing recipe, pull the diff hands with their flags and both players' action strings
(`id_action_f/t` joined to `lookup_actions`, `flg_f_cbet_def_opp`, `flg_t_cbet_opp`,
`cnt_players_f`, all-in `enum_allin`). Present the explanation to the user. Only if the user
agrees Spotlight is the correct side: add the hands to `JUSTIFIED_EXCEPTIONS` and document
the root cause in `docs/SCHEMA_NOTES.md` under a new "Spotlight oracle (Session 58+)" section.
Otherwise fix the parser or SQL through a new red → green cycle in Tasks 2–3.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml tests/test_spotlight_oracle.py docs/SCHEMA_NOTES.md
git commit -m "Add Spotlight oracle: exact hand-set match against the 9 validated recipes"
```

---

### Task 8: Live smoke test of the user's three failed questions + docs

**Files:**
- Modify: `CLAUDE.md`, `docs/STATE.md`, `docs/SPEC.md` (mark M4 status)

- [ ] **Step 1: Run the server and hit `/spot` with the three questions from Session 58**

Run in one terminal: `venv\Scripts\python -m uvicorn api:app --port 8000`
Then (PowerShell):

```powershell
$cases = @(
  @{pot="2bp"; position="ip";  role="pfr"; line="- B-?";  formation=$null},
  @{pot="3bp"; position="ip";  role="pfc"; line="vs B?";  formation=$null},
  @{pot="3bp"; position="oop"; role="pfr"; line="- B-?";  formation=$null},
  @{pot="2bp"; position="oop"; role="pfc"; line="vs B?";  formation="BB vs BTN"}
)
foreach ($c in $cases) {
  $r = Invoke-RestMethod -Method Post -Uri http://localhost:8000/spot -ContentType "application/json" -Body ($c | ConvertTo-Json)
  "$($r.interpreted_filter)"; $r.distribution | Format-Table; "hands: $($r.hands.Count)"
}
```

Expected: each returns a non-empty distribution, a hand count matching the interpreted
filter, and `hands.Count` equal to that count. Show the output to the user.

- [ ] **Step 2: Update `CLAUDE.md` Architecture for the new modules**

Add under `## Architecture`, before the frozen NL data-flow line:

```markdown
Data flow (Spotlight, active): `api.py POST /spot → spotlight.run_spot → line_parser.parse_line → spot_sql.build_spot_query → db.run_spot_query → db.get_hand_details → {interpreted_filter, distribution, hands}`

- **`line_parser.py`**: pure, no DB. `parse_line(line, role, position) -> LineSpec`. Letters belong to the preflop raiser (`-` = Hero PFR, `vs` = villain PFR); `?` marks the decision. Each heads-up street is resolved by matching the PFR's letters against every legal street sequence (`SEQUENCES`), giving exact Hero/villain PT4 action strings. Bad input raises `SpotInputError` (a `ValueError`).
- **`spot_sql.py`**: `build_spot_query(pot, position, role, spec, formation=None) -> (where_sql, params, measured_sql)`. `PREFLOP_CONTEXTS` (pot × role) reuses validated `ATOMIC_FILTERS`; `FORMATIONS` are OOP-first seat pairs over `SEATS` (6-max codes).
- **`spotlight.py`**: `run_spot(...)` orchestrates and builds the distribution (measured-set order, zero rows included) and the interpreted-filter text (`describe`). Empty results skip `get_hand_details`; NaN → `None`.
```

Also add under `## Commands`: ``- Run the DB oracle tests (need Postgres): `pytest -m db` (excluded from the default run)``.

- [ ] **Step 3: Update `docs/STATE.md` and `docs/SPEC.md`**

`SPEC.md` ladder, M4 row status: `✅ Session <N>`. `STATE.md`: current milestone = M5 (Spotlight UI), next step = the frontend bar, plus any oracle exceptions found in Task 7.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md docs/STATE.md docs/SPEC.md
git commit -m "Close M4: Spotlight core live; docs updated"
```
