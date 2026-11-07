# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-11-07, Session 71

## Current milestone

**M7 (breakdown filters) in progress; M6 run 3 started, not finished.** No in-scope fallback to PT4
so far. Whether M7 closes is still undecided.

Done this session (all pushed):
- **Picks stack as crossed sets** (`deabbf4`): actions, hand types, draw types are three sets, OR
  within, AND across. A type cell adds its type and action (removes both if both picked). With
  several actions picked, type-table cells split each type among the picked actions only.
- **Hand / Draw dropdowns removed** (`b7fd380`): a `#picks` line under the filter shows the picks,
  the hands they keep (before the Result range) and Clear. `/spot` still takes `hand_types` / `draw_types`.
- **`B` never means a donk** (`39be5ad`): `B` where only a donk fits errors, asks for `D` (or `X`).

## Next

1. **Finish M6 run 3.** The user studies with the tool; log every in-scope fallback to PT4 (the 20
   lines + breakdown filters). Then decide whether M7 closes.

## Open questions / deferred minors

- No JS tests for the picks / recount (no Node installed); verified by hand in Chrome. If it
  regresses, install Node and move the pick logic into a testable `picks.js`.
- Hand # is gone from the table; if the user misses it for PT4 lookups, show it in a row tooltip.
- `spikes/` scripts still hardcode `id_player = 10` (frozen, not fixed).
- Villain grammar minors: misleading errors on `Strat-B`, `Stratx`, `S`; interpreted filter shows no
  `vs`; `sizing.py` docstring says "only bet"; `tests/test_donk_db.py` skips flop `D` and `XC-D` IP.
- Draws: three spec calls not confirmed in GTO Wizard; no fixture for made flush + straight draw.
- `pt4_diff` stale comment + bare KeyError on `--column`; `[data-pick]:hover` outranks `.selected`;
  NULL/zero `amt_pot_<s>` labels `Bo`. Chrome caches the page: reload with Ctrl+Shift+R.

## Uncommitted work in the tree

- None. **Parked, untracked on purpose:** `docs/reports.md` + `spikes/line_volume.py`. Don't commit, don't delete.
- Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000` (no `--reload`: restart after Python changes).
