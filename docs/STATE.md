# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-09-28, Session 52

## Current milestone

**M3 closed this session.** Backend contract (Session 51) + a polished frontend
(Session 52) merged to `main` (`9c2afd8`). `static/index.html` (plain HTML/JS, no build
step, served via FastAPI `StaticFiles`) renders structured tables instead of raw JSON:
graphical cards, columns ordered chronologically per street (matching PT4's own hand
grid), hands newest first, full column set fits with no horizontal scroll. Fixed along
the way: `api.py` didn't handle the LLM's `ask_clarifying_question` tool call (500
instead of showing the question). Verified live in a real browser against Postgres +
OpenAI across all three `/query` response shapes. Full suite green (35 tests).

**M4 — next.** Build `situation` + `hero-response` registries for the remaining 20 lines
in `SPEC.md` (only the 4-recipe subset exists today), each validated by exact set
membership against PT4, same discipline as the existing `2BP`/`3BP` formulas in
`SCHEMA_NOTES.md`.

## Next

1. Start a new branch for M4 (`m4-...`), per the branch-per-milestone workflow.
2. Pick the first uncovered line from `SPEC.md`'s 20-line table and build its
   `situation`/`hero-response` pair, validated 0/0 against PT4.

## Open questions

- M4/M5 handoff: M5 needs M4's `situation` registry before it can resolve which
  hero-response applies when the LLM extends a filter turn-by-turn (no static `query_name`
  to look up in `LINES` in that path).

## Known gap (not blocking)

`main.py` (CLI, not the target) still assumes filter results are a flat table — for a
`LINES` recipe it misreports the hand count. Out of scope.

## Uncommitted work in the tree

None. `main` clean, `m3-ui` merged and can be deleted whenever convenient (not done yet).
