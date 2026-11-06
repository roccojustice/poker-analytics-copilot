# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-11-05, Session 70

## Current milestone

**M7 (breakdown filters) in progress; M6 run 3 started, not finished.** So far no in-scope fallback
to PT4: every item below is friction, not a missing answer. Whether M7 closes is still undecided.

Done this session:
- **New DB `PT4_2026_11_04_092329`.** PT4 renumbered players and hands: id 10 is now another player
  (Hero = 148938). Hero is resolved by `HERO_NAME` in `.env` (`db.hero_id()`); DB fixtures use
  `hand_no`. Unit and `-m db` suites green on the new DB (790 + 80, oracle exact).
- Hands table trimmed to 14 columns (no Hand #, Stake, or type columns); Result (BB) fits.

## Next

1. **Table picks stack within a dimension.** `typePicks[dim]` holds one type; the user wants any mix
   (e.g. 3 hand types AND 2 draw types), OR within a table, AND across. Design first; no JS tests
   for the recount yet.
2. **Then remove the Hand and Draw dropdowns.** Needs a one-click clear of the picks, and the filter
   line must show the picks and their count. Keep `hand_types` / `draw_types` in `/spot`.
3. **Decide the `B` alias for a donk.** Proposal: `2bp ip pfr B` errors with `that's a donk, write D
   (for your own cbet, write X)`. Touches `line_parser.py`, the villain-grammar spec, `DECISIONS.md`.
4. **Finish M6 run 3.** Only in-scope fallbacks count (the 20 lines + breakdown filters).

## Open questions / deferred minors

- Hand # is gone from the table; if the user misses it for PT4 lookups, show it in a row tooltip.
- `spikes/` scripts still hardcode `id_player = 10` (frozen, not fixed).
- Villain grammar minors: misleading errors on `Strat-B`, `Stratx`, `S`; interpreted filter shows no
  `vs`; `sizing.py` docstring says "only bet"; `tests/test_donk_db.py` skips flop `D` and `XC-D` IP.
- Draws: three spec calls not confirmed in GTO Wizard; no fixture for made flush + straight draw.
- `pt4_diff` stale comment + bare KeyError on `--column`; `[data-pick]:hover` outranks `.selected`;
  NULL/zero `amt_pot_<s>` labels `Bo`. Chrome caches the page: reload with Ctrl+Shift+R.

## Uncommitted work in the tree

- None. **Parked, untracked on purpose:** `docs/reports.md` + `spikes/line_volume.py`. Don't commit, don't delete.
- Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000`.
