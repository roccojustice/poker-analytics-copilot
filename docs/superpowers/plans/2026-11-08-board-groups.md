# Board Groups Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** User-defined groups of flops per dashboard, a `Board group` filter (Any / group / NOT group) on both sides of the GTO dashboards, and an editor on the page.

**Architecture:** `classify` adds two group-independent columns (`flop_ranks`, `flop_texture`) to every hand, so the GTO cache is rebuilt once and never again for group edits. A new pure-ish module `board_groups.py` owns the JSON file (load / validate / atomic save) and the membership test. `dashboards.side_matches` applies the pick, so level 1 and level 2 both get it.

**Tech Stack:** Python, pandas, FastAPI + pydantic, vanilla JS (`static/dashboards.html`), pytest.

**Spec:** `docs/superpowers/specs/2026-11-08-board-groups-design.md`

## Global Constraints

- Dashboards page only; the hands page (`static/index.html`, `/spot`) is untouched.
- Textures in a group: only `rainbow` and `two-tone`. `flop_texture` values: `rainbow`, `two-tone`, `monotone`.
- `flop_ranks` = the three ranks sorted high to low (`"J98"`, `"JJ5"`, `"A22"`), ranks from `board_types.RANKS`.
- A two-tone entry matches any two-tone flop of those ranks (no suit placement).
- `board_groups.json` at the repo root, committed, shape `{"<dashboard id>": [{"name", "boards": [{"ranks", "textures"}]}]}`; atomic writes (temp file + `os.replace`).
- Seed: `2bp_ip_pfr` / `overbet`, all `["rainbow", "two-tone"]`: `J98 J97 J96 J95 J94 J93 J92 J87 J86 J85 J84 J83 J82 J76 J75 J74 J73 J72 Q96 Q95 Q85 Q84 K96 K95`.
- Request field `board_group`: `null` or `{"name": str, "negate": bool}`. Unknown group / bad input → `SpotInputError` → 400.
- Values always bound in SQL; one-line inline comments max; strict red-then-green TDD.

## Review Focus

1. A group with **zero boards** saved and picked → filter keeps nothing (group) / everything (NOT group), no crash. Test in Task 2.
2. A **category** `flop_ranks` / `flop_texture` column (as the GTO cache stores strings) → membership still correct. Test in Task 2.
3. A pick naming a group that was **renamed or deleted** in the editor since the page loaded → 400 with the group name, page shows the error. Test in Task 3.
4. **Lowercase / unsorted** pasted ranks (`98j`) → stored as `J98`; garbage tokens (`J9`, `XYZ`) in the paste box are ignored by the page, rejected by the server. Tests in Task 2 (server).
5. A v1 pickle (no `flop_ranks`) left on disk → never read after the version bump. Test in Task 1.

---

### Task 1: Flop ranks and texture on every hand

**Files:**
- Modify: `board_types.py` (add two functions)
- Modify: `spotlight.py:137-149` (`classify` adds the columns)
- Modify: `gto_cache.py` (`CACHE_VERSION`, used in the path)
- Test: `tests/test_board_types.py`, `tests/test_spotlight.py`, `tests/test_gto_cache.py`

**Interfaces:**
- Produces: `board_types.flop_ranks(card_1, card_2, card_3) -> str`, `board_types.flop_texture(card_1, card_2, card_3) -> str` (card ids, PT4 encoding); `classify` output gains `flop_ranks`, `flop_texture` columns; `gto_cache.CACHE_VERSION = "v2"`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_board_types.py
@pytest.mark.parametrize("flop, ranks, texture", [
    ("9d8cJh", "J98", "rainbow"), ("Js5h5s", "J55", "two-tone"), ("2c2dAc", "A22", "two-tone"),
    ("ThTdTs", "TTT", "rainbow"), ("Kh7h2h", "K72", "monotone"),
])
def test_flop_ranks_and_texture(flop, ranks, texture):
    ids = [card_id(flop[i:i + 2]) for i in (0, 2, 4)]
    assert board_types.flop_ranks(*ids) == ranks
    assert board_types.flop_texture(*ids) == texture

# tests/test_spotlight.py
def test_classify_adds_flop_ranks_and_texture():
    out = spotlight.classify(fake_matches([(1, "X")]), "f")   # BLL_FLOP = Ks9d3c
    assert list(out["flop_ranks"]) == ["K93"] and list(out["flop_texture"]) == ["rainbow"]

# tests/test_gto_cache.py
def test_cache_path_is_versioned(fake_db):
    _, _, cache_dir = fake_db
    gto_cache.line_matches("2bp", "ip", "pfr", "X", ["BB vs BTN"])
    assert (cache_dir / f"gto-3-{gto_cache.CACHE_VERSION}").is_dir()
    assert not (cache_dir / "gto-3").exists()
```

(`card_id` is the helper `tests/test_spotlight.py` already uses; import it the same way.)

- [ ] **Step 2: Run, expect FAIL** — `pytest tests/test_board_types.py tests/test_spotlight.py tests/test_gto_cache.py -k "ranks or versioned"` → `AttributeError: ... flop_ranks` / `KeyError: 'flop_ranks'` / the dir assert.

- [ ] **Step 3: Implement**
  - `flop_ranks`: decode with `decode_card_id`, sort by `RANKS.index` descending, join.
  - `flop_texture`: number of distinct suits → `{3: "rainbow", 2: "two-tone", 1: "monotone"}`.
  - `classify`: two more `_board_column(matches, cards[:3], …)` entries before the drop.
  - `gto_cache.line_matches`: path dir becomes `f"{cache_key()}-{CACHE_VERSION}"`; existing tests that assert `cache_dir / "gto-3"` / `"gto-4"` update to the versioned name.

- [ ] **Step 4: Run the whole suite** — `pytest` → all pass (the dashboards `frame()` fixture has no `flop_ranks`; nothing reads it yet).

- [ ] **Step 5: Commit** — `feat(board_types): flop ranks and texture on every hand; cache v2`

---

### Task 2: `board_groups.py` — storage, validation, membership

**Files:**
- Create: `board_groups.py`, `board_groups.json` (the seed)
- Test: `tests/test_board_groups.py`

**Interfaces:**
- Consumes: `flop_ranks` / `flop_texture` columns (Task 1), `line_parser.SpotInputError`, `board_types.RANKS`.
- Produces:
  - `GROUPS_FILE = Path("board_groups.json")`, `TEXTURES = ("rainbow", "two-tone")`
  - `load(dashboard_id: str) -> list[dict]` — `[]` if file or key missing.
  - `normalize(groups: list[dict]) -> list[dict]` — validated, canonical: ranks uppercased + sorted high→low, textures in `TEXTURES` order, duplicate boards merged (textures unioned), group order kept. Raises `SpotInputError`.
  - `save(dashboard_id: str, groups: list[dict]) -> list[dict]` — normalizes, writes the whole file atomically (other dashboards' keys preserved), returns the normalized list.
  - `find(dashboard_id: str, name: str) -> dict` — exact name; `SpotInputError(f"Unknown board group: {name}")`.
  - `in_group(matches: pd.DataFrame, group: dict) -> pd.Series` (bool, same index).

- [ ] **Step 1: Write the failing tests** (monkeypatch `board_groups.GROUPS_FILE` to `tmp_path / "g.json"` in a fixture)

```python
def test_missing_file_has_no_groups(groups_file): assert board_groups.load("2bp_ip_pfr") == []

def test_save_round_trips_and_keeps_other_dashboards(groups_file):
    board_groups.save("other", [{"name": "x", "boards": [{"ranks": "AK2", "textures": ["rainbow"]}]}])
    board_groups.save("2bp_ip_pfr", [{"name": "overbet", "boards": [{"ranks": "98j", "textures": ["two-tone", "rainbow"]}]}])
    assert board_groups.load("2bp_ip_pfr") == [{"name": "overbet", "boards": [{"ranks": "J98", "textures": ["rainbow", "two-tone"]}]}]
    assert board_groups.load("other")[0]["name"] == "x"

def test_duplicate_board_merges_textures(groups_file):
    out = board_groups.normalize([{"name": "g", "boards": [{"ranks": "J98", "textures": ["rainbow"]},
                                                           {"ranks": "98J", "textures": ["two-tone"]}]}])
    assert out[0]["boards"] == [{"ranks": "J98", "textures": ["rainbow", "two-tone"]}]

@pytest.mark.parametrize("groups", [
    [{"name": "", "boards": []}],
    [{"name": "a", "boards": []}, {"name": "A", "boards": []}],
    [{"name": "g", "boards": [{"ranks": "J9", "textures": ["rainbow"]}]}],
    [{"name": "g", "boards": [{"ranks": "J9X", "textures": ["rainbow"]}]}],
    [{"name": "g", "boards": [{"ranks": "J98", "textures": []}]}],
    [{"name": "g", "boards": [{"ranks": "J98", "textures": ["monotone"]}]}],
    [{"name": "g", "boards": [{"ranks": "JJJ", "textures": ["two-tone"]}]}],
])
def test_bad_groups_error(groups): with pytest.raises(SpotInputError): board_groups.normalize(groups)

def test_failed_write_keeps_the_old_file(groups_file, monkeypatch):  # mirror gto_cache's atomic test: patch the write to raise, old content survives

def test_unknown_group_errors(groups_file): with pytest.raises(SpotInputError, match="nope"): board_groups.find("2bp_ip_pfr", "nope")

def test_membership_by_ranks_and_texture():
    m = pd.DataFrame({"flop_ranks": ["J98", "J98", "J98", "Q96"], "flop_texture": ["rainbow", "two-tone", "monotone", "two-tone"]})
    g = {"name": "g", "boards": [{"ranks": "J98", "textures": ["rainbow", "two-tone"]}, {"ranks": "Q96", "textures": ["rainbow"]}]}
    assert list(board_groups.in_group(m, g)) == [True, True, False, False]
    assert list(board_groups.in_group(m.astype("category"), g)) == [True, True, False, False]

def test_empty_group_matches_nothing():
    m = pd.DataFrame({"flop_ranks": ["J98"], "flop_texture": ["rainbow"]})
    assert not board_groups.in_group(m, {"name": "g", "boards": []}).any()

def test_seed_file_is_valid_and_has_overbet():
    data = json.loads(Path("board_groups.json").read_text())
    assert board_groups.normalize(data["2bp_ip_pfr"]) == data["2bp_ip_pfr"]
    overbet = data["2bp_ip_pfr"][0]
    assert overbet["name"] == "overbet" and len(overbet["boards"]) == 24
    assert all(b["textures"] == ["rainbow", "two-tone"] for b in overbet["boards"])
```

- [ ] **Step 2: Run, expect FAIL** — `pytest tests/test_board_groups.py` → `ModuleNotFoundError: board_groups`.
- [ ] **Step 3: Implement** `board_groups.py` per the Interfaces; `in_group` compares `flop_ranks.astype(str) + "|" + flop_texture.astype(str)` against the set of `ranks|texture` keys. Write `board_groups.json` with the seed (24 boards, canonical form, 2-space indent).
- [ ] **Step 4: Run** `pytest tests/test_board_groups.py` → PASS; `ruff check board_groups.py tests/test_board_groups.py` clean.
- [ ] **Step 5: Commit** — `feat(board_groups): groups file, validation and membership; overbet seed`

---

### Task 3: The filter in the dashboards and the API

**Files:**
- Modify: `dashboards.py` (`side_matches`, `dashboard_rows`, `line_detail`, new `group_pick`, `groups`, `save_groups`)
- Modify: `api.py` (request field, config, PUT endpoint)
- Test: `tests/test_dashboards.py`, `tests/test_api.py`

**Interfaces:**
- Consumes: `board_groups.load / save / find / in_group` (Task 2).
- Produces:
  - `dashboards.group_pick(dashboard_id, board_group: dict | None) -> tuple[dict, bool] | None` — `(group, negate)`, via `board_groups.find`.
  - `side_matches(matches, spec, filters, faced_sizes, group=None)` — `group` is `group_pick`'s result; keeps `in_group` (or `~in_group` when negate).
  - `dashboard_rows(..., board_group=None)` and `line_detail(..., board_group=None)` resolve the pick once and pass it to both sides.
  - `dashboards.save_groups(dashboard_id, groups) -> list[dict]` — checks the dashboard exists, then `board_groups.save`.
  - API: `BoardGroupPick(BaseModel)` `{name: str, negate: bool = False}`, extra fields forbidden like the other models; `DashboardRequest.board_group: BoardGroupPick | None = None` (sent to dashboards as a dict); `/dashboards/config` adds `"groups": board_groups.load(id)` to each dashboard; `PUT /dashboards/{dashboard_id}/groups` body `{"groups": [...]}` → `{"groups": <normalized>}`, `SpotInputError` → 400.

- [ ] **Step 1: Write the failing tests**
  - `tests/test_dashboards.py`: extend `frame()` with `flop_ranks="J98", flop_texture="rainbow"` defaults; monkeypatch `board_groups.GROUPS_FILE` to a tmp file holding one group `g` = `J98` rainbow.
    - `test_group_pick_filters_both_sides`: user and GTO each `pd.concat([frame(["Bs"]), frame(["X"], flop_ranks="Q96")])`; with `board_group={"name": "g", "negate": False}` both sides `pct(…, "B") == 100.0`; with `negate: True` both `0.0`.
    - `test_negated_group_is_the_exact_complement`: on one frame of mixed ranks, ids kept by `g` ∪ ids kept by `NOT g` == all ids, intersection empty (use `line_detail(...)["user"]["hands_total"]` or call `side_matches` directly).
    - `test_group_pick_reaches_line_detail`: `line_detail(..., board_group=...)` user `hands_total` counts only `J98` hands.
    - `test_unknown_group_pick_errors`: `pytest.raises(SpotInputError, match="gone")`.
    - `test_save_groups_rejects_an_unknown_dashboard`.
  - `tests/test_api.py`:
    - `test_dashboards_config_ships_each_dashboards_groups` (tmp groups file → `config["dashboards"][0]["groups"]`).
    - `test_put_groups_saves_and_returns_normalized` (`"98j"` → `"J98"`).
    - `test_put_groups_bad_input_is_a_400`.
    - `test_dashboard_accepts_a_board_group` (patched `dashboard_rows` sees `board_group == {"name": "g", "negate": True}`).
- [ ] **Step 2: Run, expect FAIL** — `pytest tests/test_dashboards.py tests/test_api.py -k "group"` → unexpected kwarg `board_group` / 405 on PUT / missing `groups`.
- [ ] **Step 3: Implement** per the Interfaces.
- [ ] **Step 4: Run** `pytest` → all pass.
- [ ] **Step 5: Commit** — `feat(dashboards): board group filter on both sides; groups API`

---

### Task 4: The page — dropdown and editor

**Files:**
- Modify: `static/dashboards.html`

**Interfaces:**
- Consumes: `CONFIG.dashboards[i].groups`, `PUT /dashboards/{id}/groups`, `board_group` in `/dashboard` and `/dashboard/line` (Task 3).

Matches the reviewed mockup (`.superpowers/brainstorm/703-1794184433/content/editor-v2.html`).

- [ ] **Step 1: Bar.** A `<select id="board-group">` after River: `Board group: Any`, then per group of the current dashboard `<name>` and `NOT <name>`; rebuilt on dashboard change and after a save (keeps the current pick if it still exists, else Any). The request body gets `board_group: null | {name, negate}`; the summary line adds `Board group: <name>` / `Board group: NOT <name>`. A link `Edit groups…` toggles the editor panel.
- [ ] **Step 2: Editor.** Working copy of the dashboard's groups. Left: group list + `+ New group` (name `new group`, `new group 2`, … unique). Right: name input, `Delete group`; 13 rank buttons A…2 (3 clicks = a board, the same rank may be clicked twice or three times; a 4th click starts over), preview, `rainbow` / `two-tone` checkboxes (both checked by default), `Add` (needs 3 ranks and ≥1 texture), `Clear`; paste box + `Add pasted` (tokens split on spaces / commas, only `/^[AKQJT2-9]{3}$/i` kept, with the checked textures); the group's boards grouped by texture set (`rainbow + two-tone`, `rainbow`, `two-tone`), each chip with `×`; `Save` (PUT, replaces the working copy with the server's normalized list, refreshes the dropdown and the rows) and `Cancel` (reload from `/dashboards/config`). A save error shows inline in the panel, the working copy is kept.
- [ ] **Step 3: Check in Chrome** (`python -m uvicorn api:app --port 8000`, `/dashboards.html`): the `overbet` seed lists 24 boards; `overbet` and `NOT overbet` change both sides' numbers and their hand counts add up to `Any`'s per line; add `Q84` rainbow, save, reload the page → still there; remove it, save. Rename a group while it is picked in the dropdown → the pick follows or falls back to Any, no error.
- [ ] **Step 4: Run** `pytest tests/test_static_config.py` → PASS (the spot-config block is unchanged).
- [ ] **Step 5: Commit** — `feat(page): board group filter and editor on the dashboards page`

---

### Task 5: DB validation, cache rebuild, docs

**Files:**
- Test: `tests/test_board_groups_db.py` (marker `db`)
- Modify: `CLAUDE.md`, `docs/STATE.md`, `docs/DECISIONS.md`

- [ ] **Step 1: Write the DB test.** For `2bp_ip_pfr` / `cbet_flop` (`X`): the `id_hand` set the dashboard's GTO side keeps under `overbet` equals a set computed **independently**: query `card_1..3` for the line's GTO hands (same `build_spot_query` / `run_spot_query` call as `gto_cache._build`), decode each with `poker_cards.decode_card_id`, and test membership with a hand-written rule in the test (sorted ranks string in the seed list, suit count in {2, 3}) — no `board_types.flop_ranks`, no `board_groups.in_group`. Also assert `overbet` ∪ `NOT overbet` = all ids, disjoint.
- [ ] **Step 2: Rebuild the cache** — `python gto_cache.py build` → prints every line with its hand count, writes `cache/<key>-v2/`. Then delete the old `cache/<key>/` dir (v1, now unused).
- [ ] **Step 3: Run** `pytest -m db tests/test_board_groups_db.py` → PASS; `pytest` → all pass.
- [ ] **Step 4: Docs.** `CLAUDE.md`: `board_groups.py` entry; `board_types` gains `flop_ranks` / `flop_texture`; `dashboards` `board_group`; the page's dropdown + editor; `gto_cache` `CACHE_VERSION`. `DECISIONS.md`: board groups as explicit board lists, not formulas; per-hand group-independent columns so edits never rebuild; action picks server-side (the two candidate entries in `STATE.md`). `STATE.md`: done + next.
- [ ] **Step 5: Commit** — `test: board groups exact set on the GTO DB; docs`
