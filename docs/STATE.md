# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-09-29, Session 53

## Current milestone

**M4 in progress** (branch `m4-situations`, local only, 2 commits ahead of `main`, not
pushed/merged — expected, M4 has 19 of 20 lines left). First `situation`/`hero-response`
line built and validated: `3bp_ip_pfc_faced_cbet_flop` (SPEC.md pre-river line #1),
raise/call/fold distribution, ships with 1065 hands (deliberate superset of PT4's 1063 —
see `DECISIONS.md` and `SCHEMA_NOTES.md` for the root-caused edge case).

Along the way, generalized `hero_responses.py` from a binary `{flag_column, actions}`
shape to ordered `{conditions: [(action_name, sql_condition), ...]}` — needed for any
raise/call/fold line, not just bet/check. `db.run_distribution_query` and
`analytics.compute_distribution` updated to match. Full suite green (37 tests).

## Next

1. Pick the next uncovered line from `SPEC.md`'s 20-line table. Easiest next pick:
   `2bp_oop_pfr` bet flop → bet/check turn — reuses the existing `turn_bet_check`
   hero-response as-is, no new distribution logic needed.
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
