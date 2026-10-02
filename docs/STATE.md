# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-01, Session 54

## Current milestone

**M4 in progress** (branch `m4-situations`, 4 commits ahead of `main`, local only —
not pushed by choice). 5 of 20 lines done, all validated by exact `hand_no` set membership
against live PT4 exports: `3bp_ip_pfc_faced_cbet_flop`, `2bp_oop_pfr_turn_cbet_opp`,
`3bp_oop_pfr_turn_cbet_opp`, `3bp_ip_pfr_turn_cbet_opp`, `2bp_ip_pfc_faced_cbet_flop`. All 4
`{2bp,3bp}x{ip,oop} pfr` `turn_cbet_opp` combos (SPEC #3/#4/#5/#7) are closed. Also
refactored `2bp_ip_pfr_turn_cbet_opp` to the simplified `2bp_*_pfr` formula (no behavior
change, verified 0/0 first). Full detail + root-caused PT4 discrepancies in
`SCHEMA_NOTES.md`; the two confirmed-settled anomaly patterns are in `DECISIONS.md`.

## Next

1. Pick the next line from `SPEC.md`'s 20-line table (15 remain). Easiest mechanical
   picks: `2bp_oop_pfc_faced_cbet_flop` (#2) and `3bp_oop_pfc_faced_cbet_flop` (#8) — same
   `flop_raise_call_fold` reuse, formulas already validated (Session 46/47). Lines #6 and
   #10 need a new situation atom (faced barrel turn / flop stab), not pure reuse.
2. Same discipline each time: build recipe → validate exact `hand_no` set vs a live PT4
   export → root-cause any gap before accepting or overriding it.

## Open questions

- M4/M5 handoff: M5 needs the `situation` registry before resolving which hero-response
  applies on a conversational filter extension (no static `query_name` to look up).
- Two PT4-export anomaly categories are now settled (flop-3bet-into-turn,
  preflop-allin-runout — see `DECISIONS.md`) — expect, don't re-litigate, on future lines
  of the same shape.

## Known gap (not blocking)

`main.py` (CLI, not the target) still misreports hand count for a `LINES` recipe. Out of
scope.

## Uncommitted work in the tree

None. Clean, 4 commits ahead of `main`, local by choice (M4 isn't done).
