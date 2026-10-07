# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-06, Session 57

## Current milestone

**M4 checkpoint merged to `main` and pushed (S57); direction under review.** 9 of 20 lines
validated; #10 not started. S57 polished all 9 line descriptions (English-only examples) and
translated `routing_eval.py` to English (user now asks in English). English baseline:
**74%** on pre-polish descriptions, **70%** on current ones (within noise). Remaining misses are
systematic: short pfc phrasings (`3bp … pfc vs cbet/vs b/vs B-B`) → `threebet`,
`2bp … pfc vs cbet` → `preflop_stats`, "face a cbet on the turn" → flop sibling.

**Open idea: a "botonera" (button panel) for spot selection.** Works like GTO Wizard: click
position + action in hand order, and that path is the filter. Then NL refines that hand set
("boards BWLL", "where I bet small"). **Spike: feasible.** Replaying PT4's per-player action
strings gives the ordered sequence for 99.90% of 150k hands. The user's example path matched
PT4 flags exactly (0 extra; 9 missing, all limper hands the flag query wrongly kept). Details in
`SCHEMA_NOTES.md` → "Per-player action strings"; reproducible scripts in `spikes/`.

## Next

1. **User decides: botonera vs the current NL-routing plan.** The user isn't sure yet and is
   worried about losing what exists. Suggested first: use the current app in a real study
   session and see whether text is enough.
2. **If botonera:** full architectural brainstorm → SPEC rewrite → plan, new branch from
   `main`. Open: replay once into an own sequence table (performance), refresh on PT4 import,
   "any position" buttons for aggregate presets, M3–M5 reshuffle.
3. **If NL continues:** parked options, unchanged: pre-router (TDD), `/query` NaN → 500 (TDD),
   legacy-recipe removal. Then M4 #10.

## Open questions

- Legacy recipes out of the LLM-routable set? (assistant: yes). Flop cbet opp as PFR (asked
  again S57; free under the botonera). SPEC "bet flop" wording for #3/#4/#5/#7.
- Post-M4: hero-response breakdown (bet-fold, check-raise). M5: "only the folds" follow-up.
- `llm_parser.py` sends the tool list twice (system prompt repr + `tools=`). Untouched.
- `origin/m4-situations` is stale at `06c30ff` (all of it is in `main`). Delete or leave it.

## Uncommitted work in the tree

None. Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000` → http://localhost:8000
