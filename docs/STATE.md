# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-11-08, Session 73

## Current milestone

**M8 GTO dashboards.** `2bp ip pfr` dashboard live on `main` (pushed, `3af722a`). This session: action
picks merged; GTO `cache_key()` once per process; **board groups** shipped (spec
`docs/superpowers/specs/2026-11-08-board-groups-design.md`): per-dashboard flop groups in
`board_groups.json` (seed `overbet`, 24 boards), `Board group` filter (Any / group / NOT) on both sides,
editor on the page, GTO cache rebuilt as `v2`, exact-set test on both DBs. Type-table row order fixed.
880 tests green.

## Next

1. **Use it in a study session** on the `overbet` group (first read: cbet on overbet boards, you 90.6% vs
   GTO 37.3%). Note what's missing.
2. Optional: GTO side covers only 6 of the 24 overbet boards (`SCHEMA_NOTES.md`, flop subset). If the
   user wants more coverage, add similar boards that exist in the GTO DB; if exact proportions matter,
   weight the GTO side with GTOw subset weights (needs the weights from the user).

## Open questions / deferred minors

- Replayer parked (needs a SPEC exception). `2bp oop pfc` dashboard blocked (Villain bot's cards only
  at showdown).
- Board-groups review minors: malformed PUT → 500 not 400; no lock on `board_groups.save`; editor silent
  no-ops (no texture ticked, rejected paste tokens), dashboard switch drops unsaved edits, `cancelEdits`
  no try/catch; `saveGroups` reads the dashboard id late; no test that a v1 pickle isn't read; nits.
- Older ledger unchanged (cache eviction, `_user_cache` unbounded, split-table cells not pickable).

## Uncommitted work in the tree

- `main` = `origin/main`. Node.js LTS installed this session (for the brainstorm mockup server).
- **Parked, untracked on purpose:** `docs/reports.md` + `spikes/line_volume.py`. Don't commit, don't delete.
