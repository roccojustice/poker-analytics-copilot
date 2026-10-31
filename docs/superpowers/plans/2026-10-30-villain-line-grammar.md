# Villain Line Grammar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Line grammar with villain-only letters, so every spot of the user's list can be typed, including the three that sent M6 run 2 back to PT4.

**Architecture:** `parse_line` keeps its signature and still returns `LineSpec`, so `spot_sql.py` is untouched for the grammar. Hero's actions come from matching the villain's string against `SEQUENCES`. The page gets new presets and a decision-street rule.

**Tech Stack:** Python, pytest, vanilla JS in `static/index.html`.

**Spec:** `docs/superpowers/specs/2026-10-30-villain-line-grammar-design.md`

## Global Constraints

- One rule: a Line is the villain's actions, by street; Hero decides right after the last one.
- One grammar: `?` and a leading `-` are rejected, never tolerated.
- `spot_sql.py` doesn't change.
- Oracle stays exact: `pytest -m db` before and after, including `tests/test_spotlight_oracle.py`.
- Bad input raises `SpotInputError`; never interpolate into SQL.
- TDD: failing assertion seen before implementing. Inline comments one line max.
- Commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Don't touch `docs/reports.md` or `spikes/line_volume.py`.

## Review Focus

- `XRs - B`, `vs xrs-b`: spaces and case are irrelevant (Task 1 test).
- Trailing or doubled dash, `XC-`, `XC--X`, and a bare `vs`: clear error, no crash (Task 1 test).
- A river Line that closes the street, `C-C-C` OOP: error, there is no street left (Task 1 test).
- `Strat` as `strat`, or with `vs`, on a wrong context: same behavior regardless of case (Task 1 test).
- OOP `C-C` enables the River dropdown although it has two tokens (Task 2 test).

---

### Task 1: Parser and migration of every Line

Parser and test migration are one task: the old Lines stop parsing the moment the parser changes.

**Files:**
- Modify: `line_parser.py`, `spotlight.py`
- Test: `tests/test_line_parser.py`, and migrate `tests/test_spot_sql.py`, `test_spotlight.py`, `test_spotlight_oracle.py`, `test_api.py`, `test_static_config.py`, `test_facing_split_db.py`, `test_sizing_db.py`, `test_draws_db.py`, `test_runout_types_db.py`, `test_flop_type_db.py`, `test_hand_strength_db.py`

**Interfaces:**
- Produces: `parse_line(line, role, position) -> LineSpec`, unchanged. `StreetSpec` gains `donk: bool = False`. `LineSpec`, `SEQUENCES`, `STREETS`, `STREET_NAMES`, `SpotInputError` stay.

- [ ] **Step 1: Baseline.** Run `pytest -m db -q`. Expected: 71 passed.

- [ ] **Step 2: Write the failing tests in `tests/test_line_parser.py`**, replacing the old-grammar ones. Pin every row:

```python
@pytest.mark.parametrize("line, role, position, streets, measured", [
    ("Rs", "pfr", "oop", [("B", "R", "S")], ("F", "C", "R")),
    ("XRs-B", "pfr", "ip", [("BC", "XR", "S"), ("", "B", None)], ("F", "C", "R")),
    ("XRs-Bl", "pfr", "ip", [("BC", "XR", "S"), ("", "B", "L")], ("F", "C", "R")),
    ("XRl", "pfr", "ip", [("B", "XR", "L")], ("F", "C", "R")),
    ("XCs-X", "pfr", "ip", [("B", "XC", "S"), ("", "X", None)], ("B", "X")),
    ("Bs", "pfc", "oop", [("X", "B", "S")], ("F", "C", "R")),
    ("D", "pfr", "ip", [("", "B", None)], ("F", "C", "R")),
    ("XC-Ds", "pfr", "ip", [("B", "XC", None), ("", "B", "S")], ("F", "C", "R")),
    ("XC-D", "pfc", "ip", [("B", "XC", None), ("", "B", None)], ("F", "C", "R")),
    ("X-B", "pfr", "ip", [("X", "X", None), ("", "B", None)], ("F", "C", "R")),
    ("C", "pfr", "oop", [("B", "C", None), ("", "", None)], ("B", "X")),
    ("C-C", "pfr", "oop", [("B", "C", None), ("B", "C", None), ("", "", None)], ("B", "X")),
    ("Strat", "pfr", "oop", [("", "", None)], ("B", "X")),
])
```

Each row asserts the completed streets + decision as `(hero, villain, size)` and `measured`. Also:
- Equal results: `vs xrs-b`, `XRs - B`, `VS XRS-B` parse like `XRs-B`; `strat`, `vs Strat` like `Strat`.
- `donk` is True on the decision street of `D` and `XC-D`, and of `XC-B`; False on `XR-B` and `X-B`.
- Errors via `pytest.raises(SpotInputError, match=...)`, one per row, role/position as in the spec:

| Line | Context | Message contains |
|---|---|---|
| `` / `vs` | any | `Line is empty` |
| `vs B?` | any | `no '?'` |
| `- B` | any | `villain's actions` |
| `XC-` / `XC--X` | pfr ip | `empty street` |
| `XC` | pfr ip | `villain acts next` |
| `C-C-C` | pfr oop | `no street left` |
| `Strat` | pfr ip, pfc oop | `OOP PFR` |
| `XR-D`, `X-D`, `XC-X-D` | pfr ip | `not a donk` |
| `D` | pfc ip | `not a donk` |
| `D` | pfr oop | `not a donk` |
| `Xs` | pfr ip | `no bet to size` |
| `XC-X-X-X` | pfr ip | `at most 3 streets` |
| `Z` | pfr ip | `unknown letter` |

- All 100 lines: a test parametrized from the presets of Task 2 lives there; here, copy `LISTS` from the prototype below into the test as a fixture so it passes before the page changes.
- SPEC equality: each new form yields these streets, taken from the old parser: `XC-X` ip = `[("B","XC"),("","X")]`, `C-C` oop as above, `X-XC-X` ip = `[("X","X"),("B","XC"),("","X")]`, `X-C` oop = `[("X","X"),("B","C"),("","")]`, `C-X` oop = `[("B","C"),("X","X"),("","")]`, `B-XC-X` ip = `[("C","B"),("B","XC"),("","X")]`.

The 100 lines, by context (names already turned into letters):

```
2bp ip pfr:  X XR D XC-X XC-XR XR-B XR-X XC-XC-X XC-XR-B XC-X-X XC-X-B
2bp ip pfc:  B X XR B-B B-X XC-X XR-B B-B-B B-XC-X XC-X-B B-X-B B-X-X XC-XC-X XC-X-X
2bp oop pfr: Strat B X BC B-B X-C B-C B-B-B B-X BC-X X-X
2bp oop pfc: B X BC B-B X-C BC-C B-B-B B-X BC-X X-X
3bp ip pfr:  X XR D XC-X X-B XR-B XR-X XC-D XC-XC-X XC-XC-XR XC-X-B XC-X-X XR-B-X XC-XC-D
3bp ip pfc:  B X B-B B-X X-X X-B B-B-B B-B-X B-XC-X B-X-X B-X-B X-XC-X X-B-B X-X-B X-X-X
3bp oop pfr: Strat R X C C-B R-B C-C C-X X-X X-C B-X R-X C-B-B C-X-B C-C-B
3bp oop pfc: B X BC B-B X-C BC-C B-B-B B-X BC-X X-X
```

- [ ] **Step 3: Run.** `pytest tests/test_line_parser.py -q`. Expected: FAIL on assertions (old grammar raises different errors).

- [ ] **Step 4: Implement in `line_parser.py`.** Remove the `-` / `?` / `vs`-by-role handling and the `_is_facing` donk filter. New helpers:

`_split_tokens(line) -> list[tuple[str, str | None]] | None`: strip whitespace, uppercase, drop a leading `VS`; empty → `Line is empty`; `STRAT` → `None`; `?` → message with `no '?'`; leading `-` → `villain's actions`; split on `-`, more than 3 → `at most 3 streets`; empty token → `empty street`; size and letter checks as today, with `D` added to `LETTERS` (first letter only).

`_resolve_street(letters, must_close) -> tuple` per spec "Hero's actions are implied": `D` is `B` for matching. A street before the last matches exactly one closed sequence. The last matches sequences whose last action is the villain's: open means same-street decision; closed requires Hero OOP and a street left. Reuse the logic in the prototype, `final_matches` / `closed_matches`.

Donk check, `_is_donk(previous_seq, street_index, hero_seat, role) -> bool`: Hero IP, the street's first action is the villain's `B`, and Hero made the last `B`/`R` of the previous street; on the flop, role is `pfr`. A typed `D` where this is False raises `not a donk`. `donk=True` is set from this check whether `B` or `D` was typed.

A closed last street produces a decision `StreetSpec(next_street, "", "", None)`; `Strat` produces flop `("", "")` and needs role `pfr` + position `oop`.

Measured: `("F","C","R")` if the decision sequence faces a bet, else `("B","X")`.

- [ ] **Step 5: `spotlight.py` `describe`.** Add a test in `tests/test_spotlight.py` that `XC-D` interpreted text contains `donk`, watch it fail, then show `villain donk B` for `donk` streets. Same text otherwise.

- [ ] **Step 6: Migrate the other tests.** Replace old Lines using the spec's "SPEC Lines in the new form". Rule per test: read role + position, then write the villain's letters. Sized: `- Bs-?` is `XCs-X` IP, `Cs` OOP. `- ?` is `Strat` OOP, `X` IP. Change Lines only; assertions stay. If an assertion must change, it's a finding: stop and report.

- [ ] **Step 7: Run.** `pytest -q` and `pytest -m db -q`. Expected: all pass; oracle exact. `tests/test_static_config.py` may fail on presets until Task 2; if so, migrate its presets in the JSON block now and leave the rest of Task 2.

- [ ] **Step 8: Commit** `feat(line): villain-only Line grammar`.

### Task 2: Page

**Files:**
- Modify: `static/index.html:76`, `:113` block, `:273-276`, `:501`
- Modify: `tests/test_static_config.py`

**Interfaces:**
- Consumes: `parse_line` from Task 1.

- [ ] **Step 1: Failing test.** In `tests/test_static_config.py`: `spot-config` presets equal the 100 lines of Task 1 plus `C` in `2bp oop pfr` and `X-XC-X` in `2bp ip pfr`, and each parses for its key. Run: FAIL.

- [ ] **Step 2: Presets and placeholder.** Update the JSON and set the placeholder to `Line, e.g. vs XR-B`.

- [ ] **Step 3: Decision street.** Test with Node if available, else by the browser step below. `lineStreets(line, position)`: drop whitespace and a leading `vs`; `strat` is 1; count tokens, plus 1 when `position === "oop"` and the last token's letters, size suffix removed, end in `C` or `X`. Update callers, and call `refreshRunoutControls` when the position toggle changes. Comment on `:273` stays one line.

- [ ] **Step 4: Header.** `:501` `Hands (% faced)` → `Hands (%)`.

- [ ] **Step 5: Browser check** with the app restarted: `2bp ip pfr` `XR-B` returns hands; OOP `C-C` enables River; `C` enables Turn and not River; IP `XC-X` enables Turn; old `vs B?` shows the error; suggestions change with the bar.

- [ ] **Step 6: Run** `pytest -q`. Expected: all pass. **Commit** `feat(page): villain Line presets and decision street`.

### Task 3: PT4 validation and docs

**Files:**
- Modify: `docs/SPEC.md`, `docs/DECISIONS.md`, `docs/SCHEMA_NOTES.md`, `CLAUDE.md`

The user provides exports in `exports/`; PT4 filters as agreed with the user per spot.

- [ ] **Step 1: Diffs**, both directions. `python pt4_diff.py <export> <pot> <pos> <role> "<line>"`:
  `2bp ip pfr XR-B`, `3bp ip pfr XR-B`, `2bp ip pfr X-B`, `2bp ip pfr XC-D`, `2bp ip pfr XRs-B`.
  Expected: 0 / 0, except hands where the bet covers Hero if the PT4 filter uses `Raise Opportunity`. Every difference gets a cause.

- [ ] **Step 2: Pin.** Add to a `db` test what the diffs proved: for `XC-D`, every hand has PT4's `flg_t_donk_def_opp`-side flag consistent with `donk` (`SCHEMA_NOTES.md` line 155 names the flags). If `D`'s rule differs from PT4's, stop and report.

- [ ] **Step 3: Docs.** `SPEC.md`: domain model, the 20 Lines, Donks out of "Deferred". `DECISIONS.md`: the grammar change and the reversed Session 58 entries. `SCHEMA_NOTES.md`: diff results. `CLAUDE.md`: `line_parser.py` bullet, page bullet, `pt4_diff` example.

- [ ] **Step 4: Run** `pytest -q` and `pytest -m db -q`. **Commit** `docs: villain Line grammar validated against PT4`.
