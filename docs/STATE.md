# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-19, Session 63

## Current milestone

**M7 (breakdown filters) in progress.** Shipped this session, merged and pushed (`a81cf64`):
- **Runout filters, M7 #6 part 2**: multi-select "Turn" and "River" on the bar (`FC`, `SC`,
  `BP high/mid/low`, `BW A/K/Q/J`, `FDP` turn only, `Brick`). Labels overlap; OR within a street,
  AND across Flop/Turn/River. Turn needs a turn/river decision, River needs a river decision
  (the control is greyed out otherwise). Rules in `specs/2026-10-19-runout-types-design.md`.
  Real-data check on `2bp IP PFR - B-?` matched theory (SC 20.8%, Brick 42.0%).

## Next

**M7 #7 Hand strength: spike first.** Does PT4 store made-hand strength per street, or only
`id_final_hand`? Find out before brainstorming (what the turn/river card does to Hero's hand:
pair, trips, nothing). Then **re-run M6** (real study session, no fallback to PT4).

## Open questions / deferred minors

- Runout: a greyed-out Turn/River control keeps its old selection and re-applies it when the
  Line comes back to that street. `_keep` filters on the joined display string, not the tuples.
  `board_types.py`: an extra blank line and long lines.
- Facing split on `- B?`: header says "% faced" but rows bucket Hero's own cbet. Decide the
  wording before the M6 re-run.
- Page: `[data-pick]:hover` outranks `.selected`. No automated test for the page click filter.
- `pt4_diff`: stale comment at line 26; no `--flop-type`/runout flags; wrong `--column` is a bare KeyError.
- Sizing: a NULL/zero `amt_pot_<s>` would label `Bo`.

## Uncommitted work in the tree

- **Parked idea, untracked on purpose:** `docs/reports.md` + `spikes/line_volume.py` (line
  volume / bb/100 report). The user's call: a separate idea, maybe later. Don't commit, don't delete.
- Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000`.
