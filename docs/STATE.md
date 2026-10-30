# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-29, Session 67

## Current milestone

**M7 (breakdown filters) in progress.** Shipped this session, merged and pushed (`61f3aba`):
- **M7 #7 part 4: draws.** GTO Wizard's 8 draw types (Combo draw, Flush draw nuts, Flush draw,
  OESD, Gutshot, BDFD 2 cards, BDFD 1 card, No draw), exclusive by priority, independent of the
  hand type (AND). Rules confirmed hand by hand in GTO Wizard by the user (20 fixtures); river =
  No draw. `draws.py` + `draw_types` filter + `draw_split` + page Draw dropdown / table / third
  cumulative pick. Validated vs PT4's draw flags, exact where the definitions agree
  (`SCHEMA_NOTES.md`, "Draws"). Spec/plan: `2026-10-29-draws*`.
- `.env` now points at `PT4_2026_10_29_075726` (the user's duplicate DB; all `db` tests pass on it).

## Next

1. **BB result filter** (last M7 breakdown): narrows the hand list only, not the distribution
   (SPEC). Brainstorm with the user first (the page already has a client-side Result from/to).
2. Then **re-run M6** (a real study session on the tool instead of PT4).

## Open questions / deferred minors

- Draws: three spec calls not confirmed in GTO Wizard (board-only straight outs don't count,
  made flush + straight draw = straight draw, nut FD + straight draw = Combo); the PT4 check's
  turn exclusions are broad (straightening boards, `n >= 3` board suit); no fixture for made
  flush + straight draw or a NaN card id; CLAUDE.md page bullet starts lowercase.
- Subcategories: `test_hand_split_top_pair_group` shows two leaves, not one; priority comment
  sits above `HAND_GROUPS`; no test that group names are rejected as `hand_types`.
- Picks: no JS tests for the recount (now three dimensions).
- Hand strength (older): cosmetics deferred; missing fixtures (SF over board flush, wheels,
  board trips). Facing split on `- B?`: "% faced" header vs Hero's own cbet; decide before M6.
- Page: `[data-pick]:hover` outranks `.selected`. `pt4_diff`: stale comment line 26, wrong
  `--column` is a bare KeyError. Sizing: NULL/zero `amt_pot_<s>` would label `Bo`.

## Uncommitted work in the tree

- **Parked idea, untracked on purpose:** `docs/reports.md` + `spikes/line_volume.py`. Don't commit, don't delete.
- Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000`.
