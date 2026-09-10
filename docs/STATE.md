# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-09-10, Session 49

## Current milestone

**M1 — Spec + doc-system switch.** Complete this session (pending the
`feedback_mentorship_style.md` compression, which is staged for user review).

## Next: M2 — Backend contract

Pilot line: **`2bp ip pfr` — B-B opportunity** (line #3 pre-river). Its data path already
exists: `2bp_ip_pfr` validated 0/0 (Session 46) + recipe `2bp_ip_pfr_turn_cbet_opp`
validated 4113/4113 (Sessions 39–40).

M2 = grow `analytics.py` to compute the action-frequency distribution over that filter →
expose as a FastAPI endpoint returning `{interpreted_filter, distribution, hand_ids}` →
validate the numbers against PT4.

## First steps of M2 (next session)

1. Define the project's git branch strategy (branch per milestone? per slice? direct to
   main?) → record in `DECISIONS.md`.
2. Then start the M2 backend contract.

## Open questions

- Git branch strategy (above).
- M4/M5 overlap: M5 can begin once M4 covers the pre-river lines — exact handoff point
  TBD.
- Frontend stack for M3 (not chosen).

## Uncommitted work in the tree

Session 48 v2 plumbing (M5 groundwork), 25/25 green, **not yet committed**:

- `db.py` — `run_filter_query` takes a prebuilt `(where_clause, params)` instead of a
  recipe name
- `query_router.py` — `run_query` gains `active_filters=None`
- `tests/test_db.py` — reworked to hand-built fragments
- `tests/test_query_router.py` — 2 new tests covering the filter branch (was zero
  coverage)

**Pending decision (raise next session):** commit this now as M5 groundwork, or leave it.
It's coherent and green; it's ahead of the ladder (M5, not M2) but not wasted. Session
48's plan wanted a test re-review first — a learning checkpoint, optional under the new
calibration.
