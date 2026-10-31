# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-30, Session 68

## Current milestone

**M7 (breakdown filters) in progress.** Session 68:
- **BB result filter validated** and merged to local `main` (`c869c23`, not pushed): `result_bb`
  float fix, `pt4_diff --result-min / --result-max`. Full diff on `3bp ip pfc vs B`; 691 of 1,065
  confirmed on the page (`SCHEMA_NOTES.md`, "Result in BB").
- **M6 run 2** fell back to PT4 for spots with Hero PFR and IP where the villain bets first.
- **Villain Line grammar** merged to local `main`, not pushed: a Line is the villain's actions;
  `D` donk, `Strat` OOP PFR. Spec/plan `2026-10-30-villain-line-grammar*`. Oracle exact, `D`
  matches PT4's donk flags, 5 PT4 diffs exact (`SCHEMA_NOTES.md`, "Line grammar validation").

## Next

1. **Re-run M6** (a real study session on the tool instead of PT4), with the villain Line. Note
   every fallback to PT4; it decides whether M7 closes.

## Open questions / deferred minors

- Villain grammar minors: misleading errors on `Strat-B`, `Stratx`, `S`; the interpreted filter
  shows no `vs` (spec says it does); `sizing.py` docstring says "only bet", the rule is first bet;
  `tests/test_donk_db.py` skips flop `D` and PFC IP `XC-D`.
- Draws: three spec calls not confirmed in GTO Wizard (board-only straight outs don't count,
  made flush + straight draw = straight draw, nut FD + straight draw = Combo); the PT4 check's
  turn exclusions are broad (straightening boards, `n >= 3` board suit); no fixture for made
  flush + straight draw or a NaN card id; CLAUDE.md page bullet starts lowercase.
- Subcategories: `test_hand_split_top_pair_group` shows two leaves, not one; priority comment
  sits above `HAND_GROUPS`; no test that group names are rejected as `hand_types`.
- Picks: no JS tests for the recount (now three dimensions).
- Hand strength (older): cosmetics deferred; missing fixtures (SF over board flush, wheels,
  board trips).
- Page: `[data-pick]:hover` outranks `.selected`. `pt4_diff`: stale comment line 26, wrong
  `--column` is a bare KeyError. Sizing: NULL/zero `amt_pot_<s>` would label `Bo`.

## Uncommitted work in the tree

- **Parked idea, untracked on purpose:** `docs/reports.md` + `spikes/line_volume.py`. Don't commit, don't delete.
- Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000`.
