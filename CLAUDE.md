# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**It documents the codebase as it is now — how to run it, its current architecture, its conventions.** For where the project is going, the milestone ladder, and the current task, see `docs/SPEC.md` (north star), `docs/STATE.md` (where we are + next step), and `docs/DECISIONS.md` (why the non-obvious calls were made). `docs/SCHEMA_NOTES.md` holds empirically-confirmed PT4 schema facts.

## Commands

- Activate the venv first if not already active (VS Code's integrated terminal does this automatically, but a plain terminal or an agent running shell commands directly does not): `venv\Scripts\activate` (PowerShell)
- Run the web app: `python -m uvicorn api:app --port 8000` → http://localhost:8000 (`python main.py` is the older CLI loop)
- Run all tests: `pytest` (verbose, and skips `db`-marked tests by default — see `addopts` in `pyproject.toml`)
- Run a single test file: `pytest tests/test_db.py`
- Run a single test: `pytest tests/test_query_router.py::<test_name>`
- Run the DB oracle tests (need Postgres): `pytest -m db` (excluded from the default run)
- Lint: `ruff check .` (no `[tool.ruff]` config yet — runs on the 88-char default)
- Required env vars (`.env`, gitignored, never commit): `OPENAI_API_KEY`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`

## Project scope

An analytics tool over a PokerTracker 4 (PT4) Postgres database — **not** a hand-history parser (it relies on PT4's already-parsed schema) and **not** a strategy/coaching tool. It answers data questions about Hero's own play (frequencies by spot, hands matching a specific spot); it does not recommend how to play.

The target (see `docs/SPEC.md`) is **Spotlight**: a local web app with a selection bar (pot / position / role / formation) plus a typed Line in poker shorthand, compiled deterministically to SQL, returning the interpreted filter, the action-frequency distribution, and the matching hands. `static/index.html` is the Spotlight page (vanilla JS, one file); the earlier NL pipeline (LLM router behind `POST /query`) is **frozen** — kept working, not extended, with no page of its own.

## Architecture

Data flow (Spotlight, active): `api.py POST /spot → spotlight.run_spot → line_parser.parse_line → spot_sql.build_spot_query → db.run_spot_query → db.get_hand_details → {interpreted_filter, distribution, hands}`

- **`line_parser.py`**: pure, no DB. `parse_line(line, role, position) -> LineSpec`. Letters belong to the preflop raiser (`-` = Hero PFR, `vs` = villain PFR); `?` marks the decision. Each heads-up street is resolved by matching the PFR's letters against every legal street sequence (`SEQUENCES`), giving exact Hero/villain PT4 action strings. Bad input raises `SpotInputError` (a `ValueError`), which `/spot` turns into a 400.
- **`spot_sql.py`**: `build_spot_query(pot, position, role, spec, formations=()) -> (where_sql, params, measured_sql)`. `PREFLOP_CONTEXTS` (pot × role) reuses validated `ATOMIC_FILTERS`; `FORMATIONS` are OOP-first seat pairs over `SEATS` (6-max codes). Selected formations are deduped and OR-ed as `(chps.position, v.position) IN (...)`, every seat bound.
- **`spotlight.py`**: `run_spot(...)` lowercases pot/position/role, orchestrates, and builds the distribution (measured-set order, zero rows included) and the interpreted-filter text (`describe`). Each distribution row and each hand's `measured_action` carry a **label**: Hero's decision-street prefix + the measured letter (`XF`/`XC`/`XR`; `B`/`X` with no prefix). Empty results skip `get_hand_details`; NaN → `None`.
- **`db.run_spot_query()`**: Hero row + the villain row (the other `flg_f_saw` player) + six `lookup_actions` joins (`h_f/t/r`, `v_f/t/r`); returns `id_hand` + `measured_action`.

Data flow (NL, frozen): `api.py POST /query` (or `main.py` CLI) `→ llm_parser.py (LLM) → query_router.py → analytics.py / db.py + filter_recipes.py → pandas → result`. `static/index.html` is the Spotlight page served by `api.py`; its Line presets and formation list live in a `<script id="spot-config">` JSON block that `tests/test_static_config.py` checks against `spot_sql.FORMATIONS` and `parse_line`.

- **`api.py`** — FastAPI app. `POST /query` parses the question, routes it, and for lines in `lines.py` returns `{interpreted_filter, distribution, hands}`; a generic exception handler turns unexpected errors into a 500 with a fixed message.
- **`lines.py` / `hero_responses.py`** — `LINES` maps each validated recipe to a hero-response; `HERO_RESPONSES` holds the ordered, mutually exclusive SQL conditions (e.g. raise / fold / call) that `analytics.compute_distribution()` counts via `db.run_distribution_query()`.

- **`queries.py`** — `AVAILABLE_QUERIES`, the single source of truth for what the LLM can route to. Each entry has a `description` + `examples`; metric entries also have `group_by_options`. Adding a queryable capability means adding an entry here (plus a matching `METRIC_CONFIGS` or `FILTER_RECIPES` entry), not new branching logic.
- **`llm_parser.py`** — `parse_user_query(user_question, active_filter_description=None)` uses **native OpenAI tool calling**. `build_tool_schemas()` turns every `AVAILABLE_QUERIES` entry into a function schema; the call uses `tool_choice="auto"` and reads `response.choices[0].message.tool_calls`. No tool selected → `{"query_name": "unknown"}`. `since_date` is emitted by the LLM as structured components (absolute `month`/`day`, relative `years`/`months`/`days`) and resolved deterministically in Python via `relativedelta` — the LLM never does date arithmetic. Filter tools also carry an `action` (`extend`/`replace`) field and there is a separate `ask_clarifying_question` tool — leftovers of the abandoned conversational-filtering plan; not consumed by `main.py`.
- **`query_router.py`** — `run_query(query_name, group_by=None, limit=None, since_date=None, active_filters=None)` dispatches into exactly one of two families and raises `ValueError` (fail-loud) if the name is unknown or a parameter doesn't apply to the matched family. Guards run before any DB call, so `tests/test_query_router.py` exercises them without Postgres.
  - **Metric queries** (`METRIC_CONFIGS`, in `analytics.py`) — grouped aggregations (`winrate`, `threebet`, `preflop_stats`), return a pandas DataFrame.
  - **Filter queries** (`FILTER_RECIPES`, in `filter_recipes.py`) — individual matching hands. The router builds `(where_clause, params)` — from `assemble_where(active_filters)` if `active_filters` is given, else `build_where_clause(query_name)` — passes them to `db.run_filter_query()`, then renders the result through `db.get_hand_details()`.
  - `is_filter_query()` lets `main.py` branch its output formatting between the two families.
- **`filter_recipes.py`** — the "recipe name → SQL WHERE fragment" responsibility, kept separate from DB execution.
  - `ATOMIC_FILTERS` — name → a SQL `WHERE`-clause fragment. Most are plain strings; parametrized ones (e.g. `total_raises`) are `lambda op, param_name: f"... {op} %({param_name})s"`.
  - `FILTER_RECIPES` — recipe name → an ordered list of items; each item is either an atomic name (plain string) or a `(atomic_name, op, value)` tuple for a parametrized atomic.
  - `build_where_clause(recipe_name)` validates the name against `FILTER_RECIPES` then delegates to `assemble_where(items)`, which walks the list, concatenates ` AND <fragment>`, and returns `(where_sql, params)` with a unique per-position `param_name`. Values are always bound, never interpolated.
- **`analytics.py`** — `analyze_metric(df, group_by, metric)` is a generic aggregation engine driven by `METRIC_CONFIGS`. Each config declares `generate_columns` (pre-aggregation), `agg` (pandas agg spec), `derived` (post-aggregation columns), `sort_by`. `get_hero_df()` lazily loads and caches Hero's full hand dataset in a module-level global (`_cached_df`) so one process round-trips Postgres once. `since_date_filter(df, since_date)` is the post-cache date filter for metric queries.
- **`db.py`** — single module-level SQLAlchemy `engine`, created once at import. `get_hero_hands()` pulls Hero's full dataset for the metrics path. `run_filter_query(where_clause, params, id_player=10, limit=None, since_date=None)` drops a prebuilt WHERE fragment into a fixed skeleton (a `hand_raise_totals` CTE + fixed `JOIN`s), adding `id_player`/`since_date`/`limit` as bound params. `get_hand_details(id_hands, id_player=10)` is the one reusable hand-detail-view function every filter's matching hands are rendered through — hand *filtering* and hand *display* are deliberately separate. It decodes cards via `poker_cards.decode_card_id` and normalizes PT4's sentinel `0` / NaN foreign keys (its "no data" convention) into display strings via `fillna()`.
- **`poker_cards.py`** — `decode_card_id()`, a pure function (no DB dependency) implementing PT4's card encoding: `card_id = suit_index*13 + rank_index + 1`, suits ordered `[c, d, h, s]`. Reverse-engineered against real data, not documented by PT4.

## Key conventions

- Config-driven registries (`AVAILABLE_QUERIES` in `queries.py`, `METRIC_CONFIGS` in `analytics.py`, `FILTER_RECIPES` / `ATOMIC_FILTERS` in `filter_recipes.py`) over `if/elif` chains — extend behavior by adding a dict entry.
- All SQL uses parameter binding (`%(name)s` + a `params` dict) for values; never interpolate user- or LLM-derived values into a query string. Recipe/query names are dict-key lookups, checked before use, so they never reach raw SQL.
- Validation of a new filter formula is by **exact set membership** against PT4's own count for that spot (`hand_no` set diff, both directions) — never a bare `COUNT(*)` match, which can hide +N/−N.
- Hero is hardcoded — single-user by design. The query functions use `id_player = 10` (the metrics path still lists `IN (10, 9580)`; id 9580 has 0 hands).
- The 9 validated recipes are Spotlight's regression oracle (`tests/test_spotlight_oracle.py`, marker `db`): exact hand-set and distribution equality.
- Tests that touch `db.py` mock the DB layer (`monkeypatch.setattr("db.pd.read_sql", ...)`) instead of hitting Postgres — see `tests/test_db.py`.
