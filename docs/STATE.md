# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-11-01, Session 69

## Current milestone

**M7 (breakdown filters) in progress; M6 run 3 started, not finished.** So far no in-scope fallback
to PT4: every item below is friction, not a missing answer. Whether M7 closes is still undecided.

Done this session, in `static/index.html` (browser-checked, no layout tests):
- Dropdowns have a fixed `9rem` width, ellipsized, full text in the tooltip (they used to jump rows).
- Hands sit right of the tables in a sticky pane that scrolls both ways, with a sticky header.

## Next

1. **Hands table columns:** the user wants to drop columns; ask which. 21 columns need 1815px, the
   pane has 1343px at 1920 wide, and Result (BB) sits off-screen.
2. **Table picks stack within a dimension.** `typePicks[dim]` holds one type; the user wants any mix
   (e.g. 3 hand types AND 2 draw types), OR within a table, AND across.
3. **Then remove the Hand and Draw dropdowns.** Needs a one-click clear of the picks, and the filter
   line must show the picks and their count (it read `351 hands` over a table of 14). Keep
   `hand_types` / `draw_types` in `/spot`.
4. **Decide the `B` alias for a donk.** Logged, not yet approved. `2bp ip pfr B` silently means a donk
   (the user meant a cbet, which is `X`). Proposal: error with `that's a donk, write D (for your own
   cbet, write X)`. Touches `line_parser.py`, the villain-grammar spec, `DECISIONS.md`.
5. **Finish M6 run 3.** Only in-scope fallbacks count (the 20 lines + breakdown filters).

## Open questions / deferred minors

- Villain grammar minors: misleading errors on `Strat-B`, `Stratx`, `S`; the interpreted filter
  shows no `vs` (spec says it does); `sizing.py` docstring says "only bet", the rule is first bet;
  `tests/test_donk_db.py` skips flop `D` and PFC IP `XC-D`.
- Draws: three spec calls not confirmed in GTO Wizard; PT4 check's turn exclusions are broad; no
  fixture for made flush + straight draw or a NaN card id.
- Subcategories, hand strength fixtures, `pt4_diff` stale comment + bare KeyError on `--column`,
  `[data-pick]:hover` outranks `.selected`, NULL/zero `amt_pot_<s>` labels `Bo`.
- Picks: no JS tests for the recount; item 2 above adds to that risk.
- Chrome caches the page: after editing `static/index.html`, reload with Ctrl+Shift+R.

## Uncommitted work in the tree

- **Commit and push first thing next session (deferred by the user):** `static/index.html` (dropdown
  width, hands pane) and `docs/STATE.md`, as two commits on `main`.
- **Parked idea, untracked on purpose:** `docs/reports.md` + `spikes/line_volume.py`. Don't commit, don't delete.
- Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000`.
