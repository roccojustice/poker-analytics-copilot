# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-09-16, Session 51

## Current milestone

**M3 — Minimal usable UI, in progress.** Distribution-query routing designed and built
on branch `m3-ui` (not merged — milestone isn't closed): `lines.py` (`LINES` registry,
recipe→hero-response), `query_router.has_distribution()`, the *filter* branch of
`run_query()` now returns `{interpreted_filter, distribution, hands}` for recipes in
`LINES`. `api.py`'s generic `/query` serves this shape; M2's pilot endpoint retired.
Verified end-to-end against real Postgres + real OpenAI — matches M2's validated numbers
(4113 hands, 1818 bet / 2295 check). Full suite green (33 tests), test-first throughout.

## Next: finish M3

1. Choose a frontend stack (still undecided).
2. Build the minimal UI against `/query`.
3. Close condition: 3–4 real NL questions producing filter + distribution + hand list
   through the UI.

## Open questions

- Frontend stack.
- M4/M5 handoff: M5 needs M4's `situation` registry before it can resolve which
  hero-response applies when the LLM extends a filter turn-by-turn (no static `query_name`
  to look up in `LINES` in that path).

## Known gap (not blocking)

`main.py` (CLI, not the target) still assumes filter results are a flat table — for a
`LINES` recipe it misreports the hand count. Out of scope.

## Uncommitted work in the tree

None. `main` is clean, matches `origin/main`. All M3 work is on `m3-ui` (2 commits, local
only — left unpushed by choice; merge to `main` when M3 closes).
