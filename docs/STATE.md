# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-04, Session 56

## Current milestone

**M4 in progress, paused for LLM routing** (branch `m4-situations`, 11 commits ahead of `main`,
pushed to `origin/m4-situations` S56). 9 of 20 lines validated against PT4; #10 not started.
Session 56 built `routing_eval.py` (user's real study-session questions per line, N=2, reports
hit % + misroutes) and moved routing **55% → 70%** (62/88): clarifying tool gated on an active
filter (`0a5b49a`), line descriptions rewritten identifier-first (`6bf8edb`). Two `threebet`
description rewrites were tried and reverted (both ≤ 70%; negation listing jargon made it worse).

## Next

1. **Decide the order (user leans descriptions, assistant recommends pre-router first):**
   - **Pre-router (TDD):** regex `(2bp|3bp|srp) (ip|oop) (pfr|pfc)` in the question → offer only
     line tools (drop `threebet`/`preflop_stats`). Remaining misses are 17/26 "3bp … pfc" →
     `threebet` + 4 "2bp ip pfc" short → `preflop_stats`; text tuning plateaued at 70%.
   - **More description polish:** sibling confusion #6 → #1 ("cbet en el turn" → flop line).
2. After each change: `venv\Scripts\python routing_eval.py`. Baseline runs move ~±5% between
   runs (frontier phrases flip at temperature=0) — only trust larger or systematic shifts.
3. Then: `/query` NaN → 500 bug (TDD), then M4 #10.

## Open questions

- **Legacy recipes** (`check_river_2bp_ip_pfr`, `fold_to_3bet_preflop`,
  `fold_vs_small_cbet_2bp_oop_pfc`): remove from the LLM-routable set? Assistant recommends yes
  (the latter silently stole "2bp oop pfc vs cbet" after fix 1). User's call.
- **Flop cbet opportunity as PFR** (bet/check flop): user asked for it naturally, not in the 20
  lines; today it silently routes to the turn line. Add as a line, or must return "no line"?
- `SPEC.md` table says "bet flop" for #3/#4/#5/#7 — means *precondition*, reads as flop cbet.
  Reword to `B-B opp (turn)`.
- Eval scores only `query_name`, not args (`limit=50`, "ayer" possibly → `since_date`).
- M4/M5 handoff; PT4 preflop-allin inconsistency (S54/S55) — unchanged.

## Uncommitted work in the tree

None. Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000` → http://localhost:8000
