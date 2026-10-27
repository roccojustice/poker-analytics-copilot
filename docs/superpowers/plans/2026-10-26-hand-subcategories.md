# Hand subcategories (Set, Trips, Two pair, Top pair, 2nd pair) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split five hand types into leaves grouped under their old names (same `HAND_GROUPS` + caret pattern as `Flush`), validated against PT4.

**Architecture:** `hand_strength.classify_hand` returns leaves; `HAND_GROUPS` gains five entries. `spotlight._hand_split`, the page's dropdown / caret rows / pick matching are already driven by `HAND_GROUPS` and the `spot-config` block, so the page only needs config data.

**Tech Stack:** Python 3, pandas, pytest; vanilla JS in `static/index.html`.

**Spec:** `docs/superpowers/specs/2026-10-26-hand-subcategories-design.md`

## Global Constraints

- Leaf names exactly: `Top set`, `Middle set`, `Bottom set`; `Trips Tk`, `Trips Gk`, `Trips Nk`; `Top two`, `Top + other`, `Bottom two`; `Top pair Tk`, `Top pair Gk`, `Top pair Nk`; `2nd pair Tk`, `2nd pair Gk`, `2nd pair Nk`, `2nd pair PP`.
- Group names exactly `Set`, `Trips`, `Two pair`, `Top pair`, `2nd pair`; each replaced in place in `HAND_TYPES` by its leaves in the order above.
- Kicker: ranks not on the board, high to low; kicker's index 0 → `Tk`, 1–2 → `Gk`, ≥3 or kicker on the board → `Nk`.
- `hand_types` accepts leaves only; a group name → `SpotInputError`.
- The user's rules are authoritative; PT4 validates only where it measures the same thing (spec, Validation).
- Inline comments: one line max. Strict red-then-green TDD.

## Review Focus

1. Kicker on the board (K5 on KQQ95, 5c2h on KK52): `Nk`, never an exception from `list.index`. Test in Task 1.
2. Paired boards: top pair / 2nd pair where PT4 says `2pair` (Kh9s on JJ9 → `2nd pair Gk`, Ac8d on 877 → `Top pair Tk`). Tests in Task 1; db mapping in Task 2.
3. Turn/river sets with two middle ranks (77 and TT on KT72 → `Middle set`). Test in Task 1.
4. A group with a single leaf in a result still gets its group row; existing `test_hand_split_*` for `Flush` covers the mechanism, Task 1 adds one `Top pair` case.
5. Every leaf occurs in real data per street (or is excluded with a reason) — `test_every_hand_type_occurs`, Task 2.

---

### Task 1: Classifier returns the leaves; config and existing tests follow

**Files:**
- Modify: `hand_strength.py` (`HAND_TYPES`, `HAND_GROUPS`, `classify_hand`, new helpers)
- Modify: `static/index.html` (`spot-config`: `hand_types`, `hand_groups`)
- Test: `tests/test_hand_strength.py`, `tests/test_spotlight.py`, `tests/test_api.py`

**Interfaces:**
- Produces: `HAND_TYPES` (leaves only, order per Global Constraints); `HAND_GROUPS` with `Flush` plus the five new groups in `HAND_TYPES` order; `classify_hand` / `hand_type` return a leaf.

- [ ] **Step 1: Write failing tests** in `tests/test_hand_strength.py`:
  - `test_registry_order`: the full new `HAND_TYPES` tuple and `HAND_GROUPS` dict.
  - `SUBCATEGORY_EXAMPLES` + parametrized `test_subcategories`: every row of the spec's Examples table (rainbow suits, e.g. `("KcKd", "Ks7h2d", "Top set")`), plus `("5c2h", "KsKd5d2s", "2nd pair Nk")`.
  - Rename existing expectations to leaves, from the rules: `Kh9s/JsJd9h` → `2nd pair Gk`; `TcTd/JsJd9h`, `7c7d/Ks5h2s`, `QcQd`/`JcJd`/`TcTd` on `Ks9h2s`, `9c9d/Ts8h2s`, `TcTd/QsQh6s`, `7c7h/KsKd5d5s` → `2nd pair PP`; `Ac9d/Ks9h2s` → `2nd pair Tk`; `Ah5c/Ts5s5d` → `Trips Tk`; `AcQd/QsQh5s` → `Trips Tk`; `5c5h/As2d5s` → `Middle set`; `JcTd/ThJs3s` → `Top two`; `AcTd/Th5sAs` → `Top two`; `9c8d/9s8hKs` → `Bottom two`; `Kc5h/2s2dKd5s` → `Top two`; `QcJd/Qs7h3s` → `Top pair Gk`; `Ac8d/8s7h7s` → `Top pair Tk`; `AhQh/QdJh2h` → `Top pair Tk`; `hand_type` decode test → `2nd pair Gk`. Compute any other existing row from the rules.
- [ ] **Step 2: Run** `pytest tests/test_hand_strength.py -v` → new/renamed cases FAIL with the old group names as actual values.
- [ ] **Step 3: Implement** in `hand_strength.py`: `_kicker(kicker_rank, board) -> str` (`"Tk"/"Gk"/"Nk"` per the Global Constraints rule), `_set_type(rank, board) -> str`, `_two_pair_type(ranks, board) -> str`; call them at the existing `Set`, `Trips`, `Two pair`, `Top pair` / `2nd pair` return points in `classify_hand`. The kicker is Hero's hole card other than the pair / trips rank; a pocket pair at `PAIR_POSITIONS` index 1 returns `2nd pair PP`. 3rd / 4th pair, Overpair, Underpair unchanged.
- [ ] **Step 4: Run** `pytest tests/test_hand_strength.py -v` → PASS (incl. the 20,000-sample invariant tests).
- [ ] **Step 5: Follow the backend in config and callers.** Update `spot-config` `hand_types` and `hand_groups` in `static/index.html`. In `tests/test_spotlight.py` and `tests/test_api.py`, replace group names used as `hand_types` / expected `hand_type` with the leaf the fixture's cards produce (e.g. `KcQd` on the BLL flop); the interpreted-filter test keeps its shape with leaf names. Add `test_hand_split_top_pair_group` in `tests/test_spotlight.py`: a result whose top pairs are all one leaf yields a `Top pair` row followed by that leaf with `parent: "Top pair"`.
- [ ] **Step 6: Run** `pytest` → all green (default run, `db` excluded); `ruff check .` no new findings.
- [ ] **Step 7: Commit** `feat(hand_strength): Set, Trips, Two pair, Top pair, 2nd pair subcategories`.

### Task 2: PT4 validation per street

**Files:**
- Test: `tests/test_hand_strength_db.py`
- Docs: `docs/SCHEMA_NOTES.md` (Hand strength section)

**Interfaces:**
- Consumes: Task 1's leaves and `HAND_GROUPS`.

- [ ] **Step 1: Extend `load(street)`** to also select `c.id_<s>_kicker_strength AS kicker`, and `allowed(...)` to take it.
- [ ] **Step 2: Flop mapping** (spec table): 1pair top / 2nd pair board-card pairs by kicker 1 / 2–3 / ≥4; `threeoak` used 2 strength 6/5/4 → Top/Middle/Bottom set; `2pair` 9/8/7 → Top two / Top + other / Bottom two; `(1pair|2pair, 5, 2)` → `2nd pair PP`. Run `pytest -m db tests/test_hand_strength_db.py -k agrees` → inspect any mismatch.
- [ ] **Step 3: Resolve mismatches** per the spec rule: our bug → back to Task 1's code with a new failing fixture; PT4 measuring something else → map that code to the group's leaves and note it. Expected: Trips kicker (investigate what `id_<s>_kicker_strength` means for `threeoak` first), paired-board 2pair codes.
- [ ] **Step 4: Turn and river** in `LATER`: same investigation with a crosstab of ours vs `(category, strength, used, kicker)`; map exactly where diagonal, else group-level.
- [ ] **Step 5: Run** `pytest -m db tests/test_hand_strength_db.py` → all PASS, including `test_every_hand_type_occurs` (exclude a leaf for a street only if it cannot occur, with a comment) and the `hand_split` group-sum test.
- [ ] **Step 6: Sabotage check:** flip the Gk cut to 1–3 and confirm the flop agreement test fails with a mismatch count; revert. Record the count.
- [ ] **Step 7: SCHEMA_NOTES.md:** the kicker diagonal, set / two-pair strength codes, and whatever was found for Trips and turn/river (counts, sabotage result).
- [ ] **Step 8: Commit** `test(db): hand subcategories agree with PT4; schema notes`.

### Task 3: Page check and docs

**Files:**
- Modify: `CLAUDE.md` (the `hand_strength.py` bullet: groups now include Set, Trips, Two pair, Top pair, 2nd pair; kicker rule in one line)

- [ ] **Step 1: Manual page check** (`venv\Scripts\python -m uvicorn api:app --port 8000`), spot `2bp ip pfr - B-?`: each new group row has a ▸ caret, collapsed on load and after re-run; the caret does not change the pick; clicking a group name filters to its leaves; the `Hand` dropdown nests the leaves under each group; picking only `Top pair Tk` sends that leaf and the filter line shows it.
- [ ] **Step 2: Update `CLAUDE.md`**, run `pytest` → green.
- [ ] **Step 3: Commit** `docs: hand subcategories`.
