# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-03, Session 55

## Current milestone

**M4 in progress** (branch `m4-situations`, 7 commits ahead of `main`, local by choice).
**9 of 20 lines done** (Session 54's "5 of 20" omitted #3, done in M2). All validated by exact
`hand_no` set membership against PT4. Pre-river #1–#9 closed; Session 55 added #2, #8
(`{2bp,3bp}_oop_pfc_faced_cbet_flop`, both 0/0) and #6 (`3bp_ip_pfc_faced_barrel_turn`,
new `faced_cbet_turn` atom + `turn_raise_call_fold` hero-response). Details in `SCHEMA_NOTES.md`.

## Next

1. **LLM routing eval, before fixing anything.** The user brings 2–3 real jargon questions per
   line (Spanish, as typed in a study session) → expected `query_name`, plus 2–3 genuine
   `threebet` questions. Build a script that runs each question N=5 times and reports hit %.
2. **Fix the routing:** a live smoke test showed `gpt-4o-mini` routes "3bp … pfc" and "barrel"
   questions to the `threebet` metric (#6 was never selected; #1/#8 flaky). First try
   disambiguating `threebet`'s description in `queries.py` (preflop-only, never a postflop spot);
   if that's not enough, add the jargon glossary to the system prompt. Measure before vs after.
3. **Bug (TDD):** `/query` 500s when a metric result contains `NaN` (`threebet_pct`, a
   position with 0 opportunities): JSON can't serialize it. Convert NaN → null.
4. Then resume M4: #10 (`2bp ip pfc` flop stab, needs a new atom + flop bet/check response).

## Open questions

- M4/M5 handoff: M5 needs the `situation` registry to resolve hero-response on extensions.
- PT4 included preflop-allin runouts in the `2bp_ip_pfc` export (S54) but not in `2bp_oop_pfc`
  (S55): PT4-side inconsistency, unresolved, ours is consistent.

## Known gap (not blocking)

`main.py` (CLI) misreports hand count for a `LINES` recipe. Out of scope.

## Uncommitted work in the tree

None. Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000` → http://localhost:8000
