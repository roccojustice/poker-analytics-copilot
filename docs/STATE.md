# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-11, Session 58

## Current milestone

**Direction changed: Spotlight replaces the NL router.** The user ran a real study session
on the NL app and it failed: no hands, some questions routed to `preflop_stats`. Session 58
brainstormed Spotlight end to end. Design approved section by section and written to
`docs/superpowers/specs/2026-10-11-spotlight-design.md`; `SPEC.md` rewritten (new ladder:
M4 = Spotlight core, M5 = Spotlight UI). Work lives on branch **`spotlight`**. `main` is
still the old working NL app.

## Next

1. User reviews the written spec (and the rewritten `SPEC.md`).
2. Once approved: `superpowers:writing-plans` → implementation plan for M4; the user reviews
   the plan and picks how to execute it.
3. M4 starts with `line_parser.py` under strict TDD (pure, no DB).

## Open questions

- Seat label → `chps.position` code mapping for Formations (UTG/MP codes 2–7): verify
  against the data during M4/M5.
- `origin/m4-situations` is stale at `06c30ff` (all of it is in `main`). Delete or leave it.

## Uncommitted work in the tree

None. Run the (old NL) app: `venv\Scripts\python -m uvicorn api:app --port 8000` →
http://localhost:8000
