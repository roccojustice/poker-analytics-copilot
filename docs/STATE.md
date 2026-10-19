# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-18, Session 62

## Current milestone

**M7 (breakdown filters) in progress.** Shipped this session, both merged and pushed:
- **Facing-bet split** (`cd808b0`): F/C/R decisions without a decision-street suffix label
  responses by size (`XFs`, `XCm`, …) and `/spot` returns a `split` (2D size × response table).
- **Flop type filter, M7 #6 part 1** (`75f2a3e`): the user's 8 flop types (`board_types.py`,
  spec `2026-10-18-flop-type-design.md`), multi-select "Flop" on the bar, filters distribution,
  split and hands; `Flop type` column in the hand list.

## Next

**Brainstorm the runout filters (M7 #6 part 2 / #11)**: turn and river (flush completes, turn
pairs the board, …). Same method as the flop types: the user gives definitions one by one,
then spec → plan → Native execution.

## Still open in M7

- **#7 Hand strength**: spike first — does PT4 store strength per street or only `id_final_hand`?
- Then **re-run M6** (real study session, no fallback to PT4). #4 Replay button stays deferred.

## Open questions / deferred minors

- Facing split on `- B?`: header says "% faced" but rows bucket Hero's own cbet — decide the
  wording before the M6 re-run.
- Page: `[data-pick]:hover` outranks `.selected`; unused `formations-summary/-panel` ids.
- No automated test for the page click filter (`groupsOf`); `vs Bs-B?` not in the split db SPOTS.
- `pt4_diff`: stale comment at line 26; no facing-label case; no `--flop-type`; whitespace-only
  CSV cell → spurious "missing"; wrong `--column` is a bare KeyError.
- Sizing: a NULL/zero `amt_pot_<s>` would label `Bo`. A bad flop card id fails the request even
  with Flop = Any (user's call: stay loud).

## Uncommitted work in the tree

None after this wrap-up commit. Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000`
(restart after backend changes; Ctrl+F5 after `index.html` changes).
