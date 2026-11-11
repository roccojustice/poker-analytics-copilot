# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-11-10, Session 74

## Current milestone

**M8 GTO dashboards.** `2bp ip pfr` dashboard live on `main` (pushed, `6841f82`). Between sessions the
user grew `overbet` to 37 boards and added a `small bet` group (34). This session: measured GTO
coverage of both groups (`SCHEMA_NOTES.md`: 7 / 61 and 10 / 68 board × texture keys; the user side is
~90% on boards the bot never played). User chose to keep the pooled-by-group comparison as is (no
"GTO-covered only" toggle, no coverage label). Ran a real study session on the dashboard: "all good",
no gaps reported. No code changes.

## Next

1. Decide with the user whether `2bp ip pfr` closes its part of M8 and **which spot gets the next
   dashboard** (needs a spot whose villain cards the GTO DB has; `2bp oop pfc` is blocked).
2. If the user reports gaps from further study, triage them (bug / missing / nice-to-have) first.

## Open questions / deferred minors

- Optional later: show GTO coverage on the page ("GTO: 7 of 61 keys") — declined for now.
- Replayer parked (needs a SPEC exception). `2bp oop pfc` dashboard blocked (Villain bot's cards only
  at showdown).
- Board-groups review minors: malformed PUT → 500 not 400; no lock on `board_groups.save`; editor silent
  no-ops; dashboard switch drops unsaved edits; `cancelEdits` no try/catch; no v1-pickle test.
- Older ledger unchanged (cache eviction, `_user_cache` unbounded, split-table cells not pickable).

## Uncommitted work in the tree

- `docs/STATE.md` + `docs/SCHEMA_NOTES.md` (this wrap-up) — to commit.
- **Parked, untracked on purpose:** `docs/reports.md` + `spikes/line_volume.py`. Don't commit, don't delete.
