# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-30, Session 68

## Current milestone

**M7 (breakdown filters) in progress.** Session 68:
- **BB result filter validated** and merged to local `main` (`c869c23`, not pushed): `result_bb`
  float fix, `pt4_diff --result-min / --result-max`. Full diff on `3bp ip pfc vs B`; 691 of 1,065
  confirmed on the page (`SCHEMA_NOTES.md`, "Result in BB").
- **M6 run 2** fell back to PT4 for spots with Hero PFR and IP where the villain bets first.
- **Villain Line grammar** built on branch `m7-villain-grammar`, **not merged**: a Line is the
  villain's actions; `D` donk, `Strat` OOP PFR. Spec/plan `2026-10-30-villain-line-grammar*`.
  Oracle exact, `D` matches PT4's donk flags, branch reviewed (no Critical).

## Next

1. **PT4 diffs on the branch**, exact set membership, in `exports/`: `2bp ip pfr XR-B` (413
   Spotlight hands), `3bp ip pfr XR-B` (83), `2bp ip pfr X-B` (810), `2bp ip pfr XC-D` (244),
   `2bp ip pfr XRs-B` (410). The sized one is the only proof `street_bet_sql` holds on a raised
   bet; `test_sized_labels_equal_the_suffixed_line` can't catch that. Record in `SCHEMA_NOTES.md`.
2. Merge the branch, then **re-run M6**.

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
