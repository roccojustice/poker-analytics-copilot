# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-09-11, Session 50

## Current milestone

**M2 — Backend contract: done.** `GET /distribution/2bp_ip_pfr_turn_cbet_opp` returns
`{interpreted_filter, distribution, hand_ids}`. Validated against PT4: 4113 `hand_ids`
(matches the recipe's known 4113/4113), bet/check split (1818 bet / 2295 check) confirmed
against a PT4 export. New layer: `hero_responses.py` (registry, parallel to
`filter_recipes.py`) + `db.run_distribution_query` (SQL-aggregation reusing a recipe's
validated `WHERE` clause) + `analytics.compute_distribution`. Built test-first throughout
(`superpowers:test-driven-development`). Merged to `main` (`903384e`), branch
`m2-backend-contract` deleted. Git workflow going forward: branch per milestone
(`DECISIONS.md`).

## Next: M3 — Minimal usable UI

Closes when 3–4 real NL questions each produce interpreted filter + distribution (numbers)
+ hand list.

**Open design question to resolve first:** the M2 endpoint is hardcoded, no NL routing.
`llm_parser`/`query_router` currently know only 2 query families (metric, filter) — M3
needs a 3rd: "distribution" queries resolving to a (recipe, hero-response) pair. Decide
that routing shape before touching the frontend.

## First steps of M3 (next session)

1. Design how `llm_parser`/`query_router` route to a distribution query.
2. Choose a frontend stack (still undecided).

## Open questions

- Frontend stack for M3.
- M4/M5 overlap: M5 can begin once M4 covers the pre-river lines — exact handoff point TBD.

## Uncommitted work in the tree

None — working tree clean, `main` up to date with `origin/main`.
