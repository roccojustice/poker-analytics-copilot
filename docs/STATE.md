# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-09-16, Session 51

## Current milestone

**M3 — Minimal usable UI: routing decided and implemented, frontend not started.**
Resolved the open design question from Session 50 (how `llm_parser`/`query_router` route
to a distribution query) — decided **not** to add a third dispatch family. Instead:

- New `lines.py`: `LINES` registry, `recipe_name -> hero_response_name` (the SPEC's "line"
  concept made concrete — currently one entry, `2bp_ip_pfr_turn_cbet_opp -> turn_bet_check`).
- `query_router.has_distribution(query_name)` checks `LINES` membership.
- The existing *filter* branch of `run_query()` now returns
  `{interpreted_filter, distribution, hands}` (full `get_hand_details()` table, not bare
  ids — renamed `hand_ids` -> `hands`) when the recipe is in `LINES`; unchanged
  hand-list-only behavior otherwise (the 3 pre-pivot outcome recipes — `check_river_2bp_ip_pfr`,
  `fold_to_3bet_preflop`, `fold_vs_small_cbet_2bp_oop_pfc` — stay hand-list-only: their
  filters already fix the flag that would be "distributed", so a distribution there would
  be tautological, not a real line. See design rationale in Session 51 conversation if
  revisited.)
- `api.py`'s generic `POST /query` now serializes both shapes. The M2 pilot endpoint
  (`GET /distribution/2bp_ip_pfr_turn_cbet_opp`) is retired — fully superseded.
- Built test-first (`superpowers:test-driven-development`); full suite green (33 tests).
- **Verified end-to-end against the real stack** (real Postgres, real OpenAI call, no
  mocks): a natural-language question routed correctly to `2bp_ip_pfr_turn_cbet_opp` and
  returned the same validated numbers as M2 (4113 hands, 1818 bet / 2295 check).
- Committed: `55d4fdb`.

**Known non-blocking gap:** `main.py` (CLI, pre-pivot pipeline, not the target per SPEC)
still assumes filter-family results are always a flat hand table — for a `LINES` recipe
`len(result)` prints 3 (dict keys) instead of a hand count. Not fixed; CLI isn't in scope.

## Next: M3 — Minimal usable UI

Closes when 3–4 real NL questions each produce interpreted filter + distribution (numbers)
+ hand list, through an actual UI (not just the API).

## First steps (next session)

1. Choose a frontend stack (still undecided — the one item M3's first-steps list didn't
   resolve this session).
2. Build the minimal UI against the now-working `/query` endpoint.

## Open questions

- Frontend stack for M3.
- M4/M5 overlap: M5 can begin once M4 covers the pre-river lines — exact handoff point TBD.
- Whether/how M5's dynamic filter-chaining (LLM adding atomics turn-by-turn, no static
  `query_name` to look up in `LINES`) resolves which hero-response applies — raised but not
  designed in Session 51; needs the M4 `situation` registry to exist first.

## Process note

Session 51: user requested "vibe coding" going forward — less multi-turn design
negotiation, more direct execution with a concise after-the-fact explanation. See
`feedback_mentorship_style.md` in the assistant's memory.

## Uncommitted work in the tree

None — working tree clean, `main` is 1 commit ahead of `origin/main` (not pushed;
push wasn't requested).
