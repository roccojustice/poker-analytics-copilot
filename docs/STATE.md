# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-06, Session 57

## Current milestone

**M4 merged to `main` as a stable checkpoint (S57); direction under review.** 9 of 20 lines
validated against PT4; #10 not started. S57: all 9 line descriptions polished (English-only
examples, heads-up stated, no eval questions reused), `routing_eval.py` translated to English
(user now asks in English). English baseline: **74%** on pre-polish descriptions, **70%** on
current ones — within noise. Remaining misses are systematic: short pfc phrasings
(`3bp … pfc vs cbet/vs b/vs B-B`) → `threebet`, (`2bp … pfc vs cbet`) → `preflop_stats`, and
"face a cbet on the turn as 3bp ip pfc" → flop sibling.

**Big open idea (S57): a button panel ("botonera") for spot selection**, GTO-Wizard style:
click position + action in hand order (no sizings, no board) → the path itself is the filter,
e.g. `folds to BTN → BTN R → SB F → BB C → flop BB X` = all BTN-vs-BB flop cbet opportunities.
NL then becomes refinement over that hand set ("boards BWLL", "where I bet small"). If adopted,
the LLM no longer picks the spot → pre-router and routing work become moot; the 20 lines become
presets, and their validated hand sets become the oracle for the path→SQL translator.

**Spike done, feasible** (details + PT4 facts in `SCHEMA_NOTES.md` → "Per-player action strings"):
- Replaying PT4's per-player action strings in rules-of-poker turn order reconstructs the full
  ordered sequence for **99.90% of 150k hands** (cross-checked vs PT4's `str_aggressors_*`).
  Failures seen: straddle (`S`) and 2-handed tables (different postflop order).
- User's example path vs a PT4-flag query on 100k Hero hands: **967 vs 976, 0 path-only,
  9 flag-only — all 9 had a limper** the flag query didn't exclude. The path was the more exact one.
- Not from the existing atomics (those are Hero-only precomputed flags); needs the action strings.

## Next

1. **Decide: botonera or continue the current NL-routing plan.** User hasn't decided ("fear of
   losing what we have"); suggestion: use the current app in a real study session first and see
   whether text is enough. Nothing is lost either way — `main` holds the working tool.
2. **If botonera:** full architectural brainstorm → SPEC rewrite → plan, on a new branch from
   `main`. Open design questions: (a) performance — replay once into an own sequence table,
   filter by prefix; (b) refresh when PT4 imports new hands; (c) "any position" buttons so
   presets can aggregate like `2bp ip pfr`; (d) milestone ladder M3–M5 reshuffle.
3. **If NL plan continues:** options still parked, unchanged — pre-router (TDD), `/query`
   NaN → 500 bug (TDD), legacy-recipe removal decision. Then M4 #10.

## Open questions

- **Legacy recipes** (`check_river_2bp_ip_pfr`, `fold_to_3bet_preflop`,
  `fold_vs_small_cbet_2bp_oop_pfc`): remove from the LLM-routable set? Assistant recommends yes
  (the latter silently stole "2bp oop pfc vs cbet" after fix 1). User's call.
- **Flop cbet opportunity as PFR** (bet/check flop): user asked for it naturally again (S57,
  GTO Wizard demo); not in the 20 lines. Free under the botonera.
- `SPEC.md` table says "bet flop" for #3/#4/#5/#7 — means *precondition*, reads as flop cbet.
  Reword to `B-B opp (turn)`.
- **Hero-response breakdown (bet-fold / check-raise) — post-M4 candidate.** Split `bet`/`check`
  buckets into follow-up actions (S57 ask). New `HERO_RESPONSES` entries; needs PT4 flag check
  + set-membership validation. Not in v1's 20 lines → SPEC change.
- **M5 use case (S57):** a follow-up turn filters a line's hands to one hero-response bucket
  (e.g. "only the folds"). Reuses the bucket's SQL condition from `HERO_RESPONSES`.
- `llm_parser.py` sends the tool list twice (repr in the system prompt + `tools=`). Noted, untouched.
- Eval scores only `query_name`, not args (`limit=50`, "yesterday" possibly → `since_date`).
- M4/M5 handoff; PT4 preflop-allin inconsistency (S54/S55) — unchanged.

## Uncommitted work in the tree

None. Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000` → http://localhost:8000
