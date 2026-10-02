# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-01, Session 54

## Current milestone

**M4 in progress** (branch `m4-situations`, not pushed/merged — expected, M4 has 15 of 20
lines left). Five `situation`/`hero-response` lines built and validated:
- `3bp_ip_pfc_faced_cbet_flop` (SPEC.md pre-river line #1), raise/call/fold distribution,
  ships with 1065 hands (deliberate superset of PT4's 1063 — see `DECISIONS.md` and
  `SCHEMA_NOTES.md` for the root-caused edge case).
- `2bp_oop_pfr_turn_cbet_opp` (SPEC.md pre-river line #5), bet/check distribution via the
  existing `turn_bet_check` hero-response, ships with 1292 hands (deliberate superset of
  PT4's 1294 — PT4's export turned out to have 2 false positives from an inconsistently-
  built UI filter, confirmed by direct hand inspection; see `SCHEMA_NOTES.md`). Preflop-
  context built via the Session 46 **simplified** `2bp_*_pfr` formula
  (`first_raise` + `no_limpers_faced` + `no_face_raise_preflop`, no `total_raises=1`) —
  first time that simplified form shipped in a recipe, as opposed to the IP sibling line
  which still carries the redundant `total_raises=1` condition.
- `3bp_oop_pfr_turn_cbet_opp` (SPEC.md pre-river line #4), bet/check distribution via
  `turn_bet_check`, ships with 898 hands — validated exact against a live PT4 export,
  0 extra / 0 missing, no edge case this time.
- `3bp_ip_pfr_turn_cbet_opp` (SPEC.md pre-river line #7), bet/check distribution via
  `turn_bet_check`, ships with 894 hands (deliberate superset-complement of PT4's 895 —
  1 false positive in PT4's export, same flop-3bet pattern as the OOP line's 2 hands,
  user-confirmed twice now; see `SCHEMA_NOTES.md`). This settles the flop-3bet-vs-
  `turn_cbet_opp` exclusion as a known, no-longer-case-by-case pattern.
- `2bp_ip_pfc_faced_cbet_flop` (SPEC.md pre-river line #9), raise/call/fold distribution
  via the existing `flop_raise_call_fold` hero-response, ships with 1286 hands (PT4's
  export had 1297 — 11 false positives, all preflop-allin runouts with zero flop action,
  user-confirmed none belong; see `SCHEMA_NOTES.md` for the new anomaly category —
  expect it to recur on the other `faced_cbet_flop` lines, #2/#6/#8).

Also refactored `2bp_ip_pfr_turn_cbet_opp` to the simplified `2bp_*_pfr` formula
(dropped the redundant `total_raises=1`), verified 0/0 against the old form first
(4113 hands, no behavior change) — now consistent with its OOP sibling.

Verified end-to-end in the browser (M3 UI) for the `2bp_oop_pfr_turn_cbet_opp` line —
interpreted filter, distribution (920 check / 372 bet), and matching-hands table all
rendered correctly through the real FastAPI + static UI, not just via mocked tests.

Along the way (Session 53), generalized `hero_responses.py` from a binary
`{flag_column, actions}` shape to ordered `{conditions: [(action_name, sql_condition), ...]}`
— needed for any raise/call/fold line, not just bet/check. `db.run_distribution_query` and
`analytics.compute_distribution` updated to match. Full suite green (41 tests).

**Session 54 process note:** user flagged comment bloat in `filter_recipes.py` — trimmed
multi-line narrative comments down to one-liners, full provenance lives in this file
instead (see `[[feedback_comment_discipline]]` in memory). Apply this going forward on
every new recipe.

## Next

1. Pick the next uncovered line from `SPEC.md`'s 20-line table (15 remain). All 4
   `{2bp,3bp} x {ip,oop} pfr` `turn_cbet_opp` lines are done (SPEC #3, #4, #5, #7), and
   one `faced_cbet_flop` `pfc` line is done (`2bp_ip`, SPEC #9) — `2bp_oop` (#2) and
   `3bp_oop` (#8) are the next mechanical picks, same `flop_raise_call_fold` reuse +
   already-validated Session 46/47 formulas. Lines #6 and #10 need a new situation atom
   (faced barrel turn / flop stab), not pure reuse.
2. Same discipline each time: build the recipe, validate by exact `hand_no` set
   membership against a live PT4 filter export (not just `COUNT(*)`), root-cause any gap
   before accepting or deliberately overriding it.

## Open questions

- M4/M5 handoff: M5 needs M4's `situation` registry before it can resolve which
  hero-response applies when the LLM extends a filter turn-by-turn (no static `query_name`
  to look up in `LINES` in that path).
- The `flg_f_cbet_def_opp`-based `faced_cbet_flop` atomic is now known to disagree with
  PT4's own "faced cbet" UI filter on overbet-shove-direct-folds (by design, see
  `DECISIONS.md`) — worth a quick gut-check the first time this shows up on a different
  line, in case the pattern looks different there.

## Known gap (not blocking)

`main.py` (CLI, not the target) still assumes filter results are a flat table — for a
`LINES` recipe it misreports the hand count. Out of scope.

## Uncommitted work in the tree

None. `m4-situations` clean, 2 commits ahead of `main`, not merged (M4 isn't done).
