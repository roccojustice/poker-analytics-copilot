# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-26, Session 66

## Current milestone

**M7 (breakdown filters) in progress.** Shipped this session, merged and pushed (`a01638a`):
- **M7 #7 part 3b: subcategories** of Set (top/middle/bottom), Trips / Top pair / 2nd pair
  (kicker `Tk` / `Gk` / `Nk`, plus `2nd pair PP`), Two pair (Top two / Top + other / Bottom
  two), same `HAND_GROUPS` + caret pattern as Flush. Kicker = place among ranks off the board
  (1st / 2nd–3rd / rest); a kicker outside Hero's best five is `Nk` (user, after review).
  Validated vs PT4 every street: sets / two pairs exact, Tk / Gk exact, Trips group-level only.
  Spec/plan: `2026-10-26-hand-subcategories*`.
- **Cumulative picks (page):** one action pick AND one hand pick; each table recounts
  client-side over the other pick (user's request after reviewing the app). Manual browser
  check only; no JS tests.

## Next

1. **Part 4: draws** (user flagged FD nuts and combo draws as played differently). Combo, FD
   nuts, FD, OESD, Gutshot, BDFD 2/1 cards, BDSD, No draw; exclusive by priority, independent
   of made hands; PT4 has `flg_<s>_*_draw` flags. Brainstorm the categories with the user first.
2. Then BB result filter, then **re-run M6**.

## Open questions / deferred minors

- Subcategories: `test_hand_split_top_pair_group` shows two leaves, not one; priority comment
  sits above `HAND_GROUPS`; no test that new group names are rejected as `hand_types`; spec
  builder note wrongly says `test_api` gets a 400.
- Picks: an action pick with 0 hands for the picked hand type hides that type's row (pick
  stays, list empty); no JS tests for the recount.
- Hand strength (older): cosmetic issues the user deferred (ask when cosmetics come up);
  missing fixtures (SF over board flush, wheels, board trips); `hand_type` raises on NaN/0.
- Facing split on `- B?`: header says "% faced" but rows bucket Hero's own cbet. Decide before M6.
- Page: `[data-pick]:hover` outranks `.selected`. `pt4_diff`: stale comment line 26, wrong
  `--column` is a bare KeyError. Sizing: NULL/zero `amt_pot_<s>` would label `Bo`.

## Uncommitted work in the tree

- **Parked idea, untracked on purpose:** `docs/reports.md` + `spikes/line_volume.py`. Don't commit, don't delete.
- Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000`.
