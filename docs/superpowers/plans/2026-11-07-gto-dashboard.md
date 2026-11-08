# GTO Comparison Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Dashboards page that shows, line by line for `2bp ip pfr`, the user's action frequencies next to a GTO bot database's, under Spotlight's board / sizing / hand / draw filters.

**Architecture:** Both sides run the same validated pipeline (`parse_line` → `build_spot_query` → `run_spot_query` → classification). The user side runs live. The GTO side (1.5M hands; the cbet line alone is 1,463,558 hands, 21 s of SQL and ~5 min of Python classification) is computed once into a local cache — per-line query results + per-hand classification — and filtered in pandas per request. A new `dashboards.py` holds the dashboard registry and the comparison logic; `api.py` serves it; `static/dashboards.html` is its own page.

**Tech Stack:** Python, FastAPI, pandas, SQLAlchemy/psycopg2, PT4 Postgres, vanilla JS. No new dependencies (cache uses `pandas.to_pickle`; `pyarrow` is not installed).

**Spec:** `docs/superpowers/specs/2026-11-07-gto-dashboard-design.md`

## Global Constraints

- GTO DB: `GTO_POSTGRES_DB=PT4_2026_11_07_184219`, same host/port/user/password as the user's DB; GTO player `GTO_HERO_NAME=Hero`. Both new keys go in `.env` (never committed) and in CLAUDE.md's env list.
- Never write into either PT4 database. The cache lives in `cache/` at the repo root (gitignored).
- The user side of the `2bp ip pfr` dashboard is always formation `BB vs BTN`.
- GTO numbers are exact: no sampling.
- All SQL values bound (`%(name)s`), never interpolated. Never hardcode `id_player` / `id_hand`.
- Strict TDD: red, then green, for every behavior change (memory: TDD discipline).
- One-line inline comments at most.
- Line list for `2bp ip pfr` (id → name → Line): `cbet_flop` Cbet flop `X`; `double_barrel` Double barrel `XC-X`; `triple_barrel` Triple barrel `XC-XC-X`; `vs_xr_flop` vs XR flop `XR`; `vs_probe_turn` vs probe turn `X-B`; `delayed_cbet` Delayed cbet turn `X-X`; `vs_xr_b` vs XR-B `XR-B`; `vs_donk_turn` vs donk turn `XC-D`.
- GTO hand list cap: first 200 hands of the filtered set, plus the total count.

## Review Focus

1. **Cache built from an older GTO DB** (the user re-imports more bot hands): numbers silently stale. Expected: the cache key includes the GTO DB's hand count; a mismatch rebuilds or fails loud — never serves stale data. Test in Task 3.
2. **A row with 0 hands on one side** (e.g. user has no `XR-B` hands on low flops): expected `0` hands and `—` for pct and gap, not `0.0%` and not a crash. Test in Task 4.
3. **A runout filter with a flop line** (Turn: FC selected, row Cbet flop): expected that row shows `—` with `reason`, the turn/river rows filter normally. Test in Task 4.
4. **Faced-size filter on a bet row** (S selected, row Cbet flop): expected the bet row is unaffected and flagged `size_filter_ignored`. Test in Task 4.
5. **User side drifting from the hands page**: the dashboard's user hand set for a line must equal `run_spot`'s for the same Line + `BB vs BTN` + filters. `db` test in Task 7.

---

### Task 1: DB layer takes a source (engine + player)

**Files:**
- Modify: `db.py` (engine creation, `hero_id`, `run_spot_query`, `get_hand_details`)
- Test: `tests/test_db.py`

**Interfaces:**
- Produces:
  - `db.engine` (unchanged, user DB) and `db.gto_engine()` → SQLAlchemy engine for `GTO_POSTGRES_DB`, created on first call, cached; `RuntimeError` if `GTO_POSTGRES_DB` unset.
  - `db.player_id(engine, name) -> int`, cached per `(engine.url, name)`; fails loud unless exactly one row (same message shape as today's `hero_id`). `hero_id()` becomes `player_id(engine, HERO_NAME)`.
  - `db.gto_hero_id() -> int` = `player_id(gto_engine(), GTO_HERO_NAME)`.
  - `run_spot_query(where_clause, params, measured_sql, id_player=None, engine=None)` and `get_hand_details(id_hands, id_player=None, engine=None)`: `engine=None` means `db.engine`; `id_player=None` means `hero_id()`. Callers that pass neither behave exactly as now.

- [ ] **Step 1: Write failing tests** in `tests/test_db.py` (mock `db.pd.read_sql` as the file already does):
  - `test_run_spot_query_uses_the_given_engine_and_player`: passing `engine=sentinel, id_player=42` → `read_sql` called with `sentinel` and `params["id_player"] == 42`.
  - `test_get_hand_details_uses_the_given_engine`: same for `get_hand_details`.
  - `test_player_id_fails_loud_on_zero_or_two_rows`: fake `read_sql` returning 0 rows / 2 rows → `RuntimeError`.
  - `test_gto_engine_requires_env`: `monkeypatch.delenv("GTO_POSTGRES_DB")` → `RuntimeError`.
- [ ] **Step 2:** `pytest tests/test_db.py -v` → the 4 new tests FAIL (unexpected keyword `engine` / no attribute `player_id`).
- [ ] **Step 3:** Implement the interfaces above in `db.py`.
- [ ] **Step 4:** `pytest` → all pass (existing `test_spotlight.py` monkeypatches `run_spot_query` with a 3-arg lambda; it must still pass, so `spotlight.run_spot` keeps calling it with 3 positional args).
- [ ] **Step 5:** Add `GTO_POSTGRES_DB` / `GTO_HERO_NAME` to CLAUDE.md's required env vars. Commit `feat(db): queries take an engine and a player`.

### Task 2: Split classification from filtering in `spotlight.py`

**Files:**
- Modify: `spotlight.py`
- Test: `tests/test_spotlight.py`

**Interfaces:**
- Produces:
  - `classify(matches: DataFrame, street: str) -> DataFrame`: adds `flop_type`, `turn_type`, `river_type` (same rules as today: `None` before the decision street), `hand_type`, `draw_type` (on the decision street's board); drops the card columns. No filtering.
  - `filter_types(matches, flop_types=(), turn_types=(), river_types=(), hand_types=(), draw_types=()) -> DataFrame`: today's keep rules (flop: `isin`; turn/river: label overlap via `_keep`; hand/draw: `isin`).
  - `run_spot` = `classify` then `filter_types`, otherwise unchanged. Public output identical.
- [ ] **Step 1: Failing tests:**
  - `test_classify_keeps_every_hand_and_adds_five_columns`: 3 fake rows (reuse `fake_matches` with real card ids) → 3 rows out, columns include the five, card columns gone.
  - `test_filter_types_turn_labels_overlap`: a row with `turn_type == "FC, BP high"` is kept for `turn_types=["BP high"]`, dropped for `["Brick"]`.
- [ ] **Step 2:** Run → FAIL (`classify` not defined).
- [ ] **Step 3:** Refactor `_with_board_types` / `_with_hand_and_draw` into the two functions.
- [ ] **Step 4:** `pytest` all green, then `pytest -m db tests/test_spotlight_oracle.py` → 9/9 still exact (refactor guard).
- [ ] **Step 5:** Commit `refactor(spotlight): classify apart from filtering`.

### Task 3: GTO cache

**Files:**
- Create: `gto_cache.py`
- Modify: `.gitignore` (add `cache/`)
- Test: `tests/test_gto_cache.py`

**Interfaces:**
- Consumes: Task 1 (`gto_engine`, `gto_hero_id`, `run_spot_query(..., id_player, engine)`), Task 2 (`classify`).
- Produces:
  - `CACHE_DIR = Path("cache")`.
  - `cache_key() -> str`: `f"{GTO_POSTGRES_DB}-{hand_count}"` where `hand_count = SELECT count(*) FROM cash_hand_summary` on the GTO engine.
  - `line_matches(pot, position, role, line, formations) -> DataFrame` with columns `id_hand`, `measured_action` (raw letter + size letter, as `run_spot_query` returns) plus the classification columns for that Line's decision street. Loaded from `cache/<key>/<slug>.pkl` (slug = pot_position_role_line with `-` kept); on miss: run the SQL on the GTO engine, `classify` in a `multiprocessing.Pool` (chunks of 50k rows), store, return.
  - CLI `python gto_cache.py build` is added in Task 4 (it needs `DASHBOARDS`): builds every line of every dashboard, prints per-line hand count and time.
  - String columns stored as `category` dtype (memory: 1.46M rows).
- [ ] **Step 1: Failing tests** (no DB; monkeypatch `gto_cache.run_spot_query`, `gto_cache.cache_key`, `CACHE_DIR` → `tmp_path`):
  - `test_miss_queries_classifies_and_stores`: first call queries once and writes one `.pkl`.
  - `test_hit_does_not_query`: second call with the same key → query fake not called.
  - `test_new_key_rebuilds` (Review Focus 1): change `cache_key` return → query called again, new subdirectory.
  - `test_classification_matches_spotlight`: cached columns equal `spotlight.classify` on the same fake rows.
- [ ] **Step 2:** Run → FAIL (module missing).
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** `pytest tests/test_gto_cache.py -v` → PASS.
- [ ] **Step 5:** Commit `feat(gto): cache the GTO lines and their classification`.

### Task 4: Dashboard registry and rows

**Files:**
- Create: `dashboards.py`
- Test: `tests/test_dashboards.py`

**Interfaces:**
- Consumes: Task 2 (`classify`, `filter_types`), Task 3 (`line_matches`), `spotlight._distribution`, `spot_sql.splits_by_size`, `line_parser.parse_line`.
- Produces:
  - `DASHBOARDS = {"2bp_ip_pfr": {"name": "2BP IP PFR", "pot": "2bp", "position": "ip", "role": "pfr", "formations": ["BB vs BTN"], "lines": [{"id", "name", "line"}, … the 8 from Global Constraints, in that order]}}`.
  - `user_matches(dashboard, line, date_from, date_to) -> DataFrame`: same columns as `line_matches`, from the user DB live (`build_spot_query` + `run_spot_query` + `classify`).
  - `dashboard_rows(dashboard_id, flop_types=(), turn_types=(), river_types=(), faced_sizes=(), date_from=None, date_to=None) -> list[dict]`, one per line:
    `{"id", "name", "line", "street", "measured", "user": side, "gto": side, "gap": {action: pts|None}, "reason": str|None, "size_filter_ignored": bool}`;
    `side = {"hands": int, "distribution": [rows as spotlight._distribution]}`.
  - Rules: `faced_sizes` (subset of `"SMLO"`) keeps hands whose label's size letter is in it, only on rows where `splits_by_size(spec)`; other rows get `size_filter_ignored=True` when `faced_sizes` is non-empty. A turn (river) filter on a row whose decision street is earlier → both sides `None`, `reason="Turn filter needs a turn or river decision"` (river likewise). Gap = user pct − GTO pct per measured action and per `B` size sub-row, rounded to 0.1; `None` if either side has 0 hands. Date range filters only the user side.
- [ ] **Step 1: Failing tests** (monkeypatch `dashboards.user_matches` / `dashboards.line_matches` with fake frames):
  - `test_rows_follow_the_registry_order`.
  - `test_gap_is_user_minus_gto`: user B 40% / GTO B 52% → `gap["B"] == -12.0`.
  - `test_zero_hands_side_gives_none_gap` (Review Focus 2).
  - `test_turn_filter_blanks_flop_rows` (Review Focus 3).
  - `test_faced_size_filters_response_rows_only` (Review Focus 4): S keeps only `?s` labels on `X-B`; `cbet_flop` unchanged and `size_filter_ignored`.
  - `test_every_registry_line_parses`: each Line passes `parse_line(line, role, position)`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement, plus the `gto_cache.py build` CLI (Task 3).
- [ ] **Step 4:** `pytest tests/test_dashboards.py -v` → PASS.
- [ ] **Step 5:** Commit `feat(dashboards): GTO vs user rows for 2bp ip pfr`.

### Task 5: Line detail

**Files:**
- Modify: `dashboards.py`
- Test: `tests/test_dashboards.py`

**Interfaces:**
- Produces: `line_detail(dashboard_id, line_id, flop_types=(), turn_types=(), river_types=(), faced_sizes=(), hand_types=(), draw_types=(), date_from=None, date_to=None) -> dict`:
  `{"line": {"id","name","line"}, "user": detail, "gto": detail}`, `detail = {"hands_total": int, "distribution", "split" (spotlight._split or None), "hand_split", "draw_split", "hands": list[dict]}`.
  Hand / draw picks are applied server-side (the GTO side cannot go to the browser). `user.hands` = all, rendered via `get_hand_details` on the user engine; `gto.hands` = first 200 by `id_hand` via `get_hand_details(..., id_player=gto_hero_id(), engine=gto_engine())`. Unknown `line_id` / `dashboard_id` → `SpotInputError`.
- [ ] **Step 1: Failing tests:** `test_detail_has_both_sides_with_the_same_shape`, `test_gto_hands_capped_at_200_with_total`, `test_hand_pick_filters_both_sides`, `test_unknown_line_id_errors`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement, reusing `_distribution`, `_split`, `_hand_split`, `_draw_split`.
- [ ] **Step 4:** PASS.
- [ ] **Step 5:** Commit `feat(dashboards): line detail, user and GTO side by side`.

### Task 6: API

**Files:**
- Modify: `api.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Produces:
  - `GET /dashboards/config` → `{"dashboards": [{"id","name","lines":[…]}], "flop_types", "turn_labels", "river_labels", "sizes": ["S","M","L","O"]}`.
  - `POST /dashboard` body `DashboardRequest(dashboard, flop_types, turn_types, river_types, faced_sizes, date_from, date_to)`, `extra="forbid"` → `{"rows": dashboard_rows(...)}`.
  - `POST /dashboard/line` body `LineDetailRequest` = the above + `line_id`, `hand_types`, `draw_types` → `line_detail(...)`.
  - `SpotInputError` → 400 `{"error": msg}`, as `/spot`.
  - Routes registered before the `StaticFiles` mount.
- [ ] **Step 1: Failing tests** (TestClient, monkeypatch `api.dashboard_rows` / `api.line_detail`): golden path for each route, unknown field → 422, `SpotInputError` → 400.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS.
- [ ] **Step 5:** Commit `feat(api): dashboard endpoints`.

### Task 7: DB validation

**Files:**
- Create: `tests/test_dashboards_db.py` (marker `db`)

- [ ] **Step 1:** `test_user_side_equals_hands_page` (Review Focus 5): for every registry line, `set(user_matches(...).id_hand)` == hand set behind `run_spot("2bp","ip","pfr", line, ["BB vs BTN"])`, exact.
- [ ] **Step 2:** `test_gto_preflop_context_is_the_hero_bot`: on the GTO engine, `assemble_where(PREFLOP_CONTEXTS[("2bp","pfr")] + ["heads_up_flop", "ip_flop"])` over `cash_hand_player_statistics chps JOIN cash_hand_summary chs` returns exactly the `Hero` bot's 1,500,000 `id_hand`s (set equality with all its hands) and 0 rows for the `Villain` bot.
- [ ] **Step 3:** `pytest -m db tests/test_dashboards_db.py` → PASS.
- [ ] **Step 4: PT4 export diff (needs the user):** user exports from PT4 (GTO DB active) the hand list for BTN open, BB call, flop checked to Hero, Hero bets. Run `python pt4_diff.py <export.csv> 2bp ip pfr "X" --formation "BB vs BTN" --label B` with `POSTGRES_DB`/`HERO_NAME` pointed at the GTO DB → expect 0 extra / 0 missing. Record in `SCHEMA_NOTES.md`.
- [ ] **Step 5:** Commit `test(dashboards): user side equals hands page; GTO context exact`.

### Task 8: Dashboards page

**Files:**
- Create: `static/dashboards.html`
- Modify: `static/index.html` (nav link only)
- Test: manual in Chrome (no Node, no JS tests — STATE open question)

**Interfaces:**
- Consumes: Task 6 endpoints.
- Produces: page at `/dashboards.html`; both pages share a top nav `Manos | Dashboards`.

- [ ] **Step 1:** Level 1: dashboard selector (one entry now), Flop / Turn / River checkbox dropdowns (copy `multiSelect` from `index.html`), S/M/L/O toggle, From/To (labelled "your hands"), filter line saying `BB vs BTN`. Table: one row per line; per measured action `yours | GTO | gap` cells; B rows with collapsible `Bs…Bo` sub-rows; hand counts per side; `—` + tooltip `reason` for blanked rows; greyed size cells when `size_filter_ignored`. Gap coloured only by sign, no thresholds.
- [ ] **Step 2:** Level 2 (click a row): own view, ← Back restores level 1 with its filters. Hand type × action and draw type × action tables with `yours | GTO` per cell; size × response table when `split`; clicking a type row re-requests with `hand_types` / `draw_types` (picks line + Clear, as the hands page); hand lists for both sides using `renderCards` (four-colour tiles) and the same columns as the hands page; GTO list shows "200 of N".
- [ ] **Step 3:** Run `python gto_cache.py build` once; then `python -m uvicorn api:app --port 8000`; verify in Chrome: Low flop filter changes every row; Turn FC blanks flop rows; S greys bet rows; a line's detail opens and Back returns; a hand-type pick filters both sides. Each refresh under ~3 s.
- [ ] **Step 4:** Commit `feat(page): dashboards page`.

### Task 9: Docs

- [ ] Update CLAUDE.md (architecture: `dashboards.py`, `gto_cache.py`, the endpoints, `dashboards.html`; command `python gto_cache.py build`), `docs/DECISIONS.md` (GTO side precomputed; why: 21 s SQL + ~5 min classification measured Session 72), `docs/STATE.md`. Commit `docs: GTO dashboard`.
