# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Activate the venv first if not already active (VS Code's integrated terminal does this automatically, but a plain terminal or an agent running shell commands directly does not): `venv\Scripts\activate` (PowerShell)
- Run the app: `python main.py`
- Run all tests: `pytest` (verbose by default — see `addopts = "-v"` in `pyproject.toml`)
- Run a single test: `pytest tests/test_analytics.py::test_analyze_metrics`
- Run a single test file: `pytest tests/test_db.py`
- Lint: `ruff check .`
- Required env vars (`.env`, gitignored, never commit): `OPENAI_API_KEY`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`

## Project scope

A natural language analytics agent over a PokerTracker 4 (PT4) Postgres database — not a hand history parser (relies on PT4's already-parsed schema) and not a strategy/coaching tool. It answers data questions about Hero's own play (e.g. winrate by position, 3Bet%, hands matching a specific spot), it does not recommend how to play.

## Architecture

Data flow: `User → llm_parser.py (LLM) → query_router.py → analytics.py / db.py → pandas → result`

- **`llm_parser.py`** — `parse_user_query()` sends the user's question plus every entry in `AVAILABLE_QUERIES` to the OpenAI API (`gpt-4o-mini`) and gets back JSON: `{"query_name": ..., "group_by": ...}` for aggregations, or `{"query_name": ..., "limit": ...}` for hand filters. `AVAILABLE_QUERIES` is the single source of truth for what the LLM can route to — adding a new queryable capability means adding an entry here, in matching `METRIC_CONFIGS`/`FILTER_QUERIES`, and in `query_router.py`'s dispatch, not new branching logic.
- **`query_router.py`** — `run_query(query_name, group_by=None, limit=None)` dispatches into exactly one of two families and raises `ValueError` (fail-loud, not fail-silent) if the query name is unknown or if a parameter doesn't apply to the matched family (e.g. `limit` on a metric query, `group_by` on a filter query). These guards run before any DB call, which is why `tests/test_query_router.py` can exercise them without Postgres.
  - **Metric queries** (`METRIC_CONFIGS`, in `analytics.py`) — grouped aggregations (`winrate`, `threebet`, `preflop_stats`), return a pandas DataFrame.
  - **Filter queries** (`FILTER_QUERIES`, in `db.py`) — individual matching hands, returned as a structured table via `get_hand_details()`.
  - `is_filter_query()` lets `main.py` branch its output formatting between the two families.
- **`analytics.py`** — `analyze_metric(df, group_by, metric)` is a generic aggregation engine driven by `METRIC_CONFIGS`. Each config entry declares: `generate_columns` (pre-aggregation, e.g. `bb_won = amt_won / amt_bb`), `agg` (pandas agg spec), `derived` (post-aggregation columns, e.g. `bb_per_100 = avg_bb_per_hand * 100`), and `sort_by`. `get_hero_df()` lazily loads and caches Hero's full hand dataset in a module-level global (`_cached_df`) so one process only round-trips Postgres once, no matter how many metric queries run in that session.
- **`db.py`** — single module-level SQLAlchemy `engine`, created once at import (not per function call). `FILTER_QUERIES` maps a filter name to a SQL `WHERE`-clause fragment; `run_filter_query()` wraps whichever fragment matches `filter_name` inside a fixed skeleton (a `hand_raise_totals` CTE + fixed `JOIN`s), with `id_player`/`limit` passed as bound params, never string-interpolated. `filter_name` itself is checked against `FILTER_QUERIES.keys()` before use — it's a dict-key lookup, so it never reaches raw SQL. `get_hand_details(id_hands, id_player)` is the one reusable hand-detail-view function every filter's matching hands are rendered through — hand *filtering* and hand *display* are deliberately separate responsibilities. It also normalizes PT4's sentinel `0` foreign keys (its convention for "no data," e.g. no showdown, hand didn't reach a street) into display strings via `fillna()`.
- **`poker_cards.py`** — `decode_card_id()`, a pure function (no DB dependency) implementing PT4's card encoding: `card_id = suit_index*13 + rank_index + 1`, suits ordered `[c, d, h, s]`. Reverse-engineered against real data, not documented by PT4.

## Key conventions

- Config-driven registries (`METRIC_CONFIGS`, `FILTER_QUERIES`, `AVAILABLE_QUERIES`) over `if/elif` chains — extend behavior by adding a dict entry.
- All SQL uses parameter binding (`%(name)s` + a `params` dict) for values; never interpolate user- or LLM-derived values directly into a query string.
- Hero is hardcoded as `id_player IN (10, 9580)` in `db.py` — this is a single-user MVP, not built for multi-user access.
- Tests that touch `db.py` mock the DB layer (`monkeypatch.setattr("db.pd.read_sql", ...)`) instead of hitting Postgres — see `tests/test_db.py`.
