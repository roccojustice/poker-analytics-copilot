# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-11-08, Session 73

## Current milestone

**M8 GTO dashboards.** `2bp ip pfr` validated and merged to `main` + pushed: PT4 export diff on the GTO DB
0/0 (761,697 hands, `SCHEMA_NOTES.md`), the three JS review fixes verified in Chrome. New this session,
on branch `feat/dashboard-action-picks` (local, not merged): **action picks** in a line's detail
(Bet / Bet small… / Check rows filter both hand lists and the hand / draw tables; server-side `actions`
in `line_detail`). 837 tests green, checked in Chrome.

## Next

1. Merge `feat/dashboard-action-picks` into `main` and push (user OK'd the feature; not yet merged).
2. **Board groups (design agreed in chat, not written yet):** write the spec in
   `docs/superpowers/specs/`, then plan, then build. Agreed so far:
   - Goal: compare the user's frequencies vs GTO on a user-defined group of flops (e.g. his "overbet
     boards"), because BLL boards split between GTO-overbet and GTO-small and the check % differs.
   - A group = name + list of entries `{ranks (e.g. "Q96", pairs allowed), suit textures (rainbow /
     two-tone / monotone; "ALL" = any)}`; texture is per entry. Stored server-side in a JSON file
     (e.g. `board_groups.json`), editable on the dashboards page (13-rank picker, 3 clicks = one
     board, texture checkboxes, list with ×, save / rename / delete). Maybe a paste box ("J98 J97 …").
   - Filter: "Board group" dropdown (Any / <group> / NOT <group>) on Dashboards only (not the hands
     page), both sides, AND with Flop/Turn/River and picks.
   - GTO cache needs the flop's ranks + texture per hand → rebuild (~4 min).
   - User's current rule, expanded (to seed the first group "overbet"): ALL: J98 J97 J96 J95 J94 J93
     J92, J86 J85 J84 J83 J82, J87 J76 J75 J74 J73 J72; rainbow or two-tone: Q96 Q95 Q85 Q84 K96 K95.
   - Still to confirm with the user: the editor playback (last message) was not reviewed.

## Open questions / deferred minors

- Replayer parked (option B; needs a SPEC exception to "no HH parsing"). `2bp oop pfc` dashboard blocked
  (Villain bot's cards only at showdown).
- Candidate DECISIONS entries (confirm wording first): action picks are server-side because only 200
  GTO hands reach the page; board groups as explicit board lists, not formulas like "2grap".
- Review minors ledger unchanged (cache eviction, `_user_cache` unbounded, etc.); split-table cells
  are not pickable yet.

## Uncommitted work in the tree

- `main` = `origin/main`. `feat/dashboard-action-picks` is local only (1 commit).
- **Parked, untracked on purpose:** `docs/reports.md` + `spikes/line_volume.py`. Don't commit, don't delete.
