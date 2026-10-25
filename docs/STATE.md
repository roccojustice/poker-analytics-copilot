# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-24, Session 65

## Current milestone

**M7 (breakdown filters) in progress.** Shipped this session, merged to `main` (`e9d41e9`):
- **User review of hand strength** in the app: functionality OK; cosmetic issues exist, deferred
  by the user ("los resolvemos más adelante"), not yet listed — ask for them when cosmetics come up.
- **M7 #7 part 3a: Nut flush vs Other flush.** `HAND_TYPES` has the two leaves, `HAND_GROUPS`
  groups them as `Flush` (breakdown group row + ▸ caret sub-rows, grouped `Hand` dropdown). Nut =
  Hero's highest suited hole card is the highest rank of the suit off the board. Validated vs PT4
  flush strength (10 = nut): 0 mismatches f/t/r. Spec/plan: `2026-10-24-nut-flush*`.
  Samples are small (all hands: ~56 flop / 162 turn / 270 river nut flushes).

## Next

1. **M7 #7 part 3, rest: subcategories of Set, Two pair** (or others), defined one by one with
   the user, same group pattern (`HAND_GROUPS` + caret). Ask first which ones he actually wants;
   he only wanted two flush buckets, not nut/2nd/3rd.
2. **Part 4: draws** (user flagged FD nuts and combo draws as played differently). Combo, FD nuts,
   FD, OESD, Gutshot, BDFD 2/1 cards, BDSD, No draw; exclusive by priority, independent of made
   hands; PT4 has `flg_<s>_*_draw` flags.
3. Then BB result filter, then **re-run M6**.

## Open questions / deferred minors

- Nut flush: dropdown summary "Hand: Flush" vs filter line "Hand: Nut flush, Other flush";
  collapsing Flush with a leaf picked hides the highlight (list stays filtered); no JS test.
- Hand strength: board quads + A = Ace high (assistant's call); missing fixtures (SF over board
  flush, wheels, board trips, three pairs on river); `hand_type` raises on NaN/0 hole card;
  disabled Turn/River keep a stale selection; hand-table row pick only on the name.
- Facing split on `- B?`: header says "% faced" but rows bucket Hero's own cbet. Decide before M6.
- Page: `[data-pick]:hover` outranks `.selected`. `pt4_diff`: stale comment line 26, wrong
  `--column` is a bare KeyError. Sizing: NULL/zero `amt_pot_<s>` would label `Bo`.

## Uncommitted work in the tree

- **Parked idea, untracked on purpose:** `docs/reports.md` + `spikes/line_volume.py`. Don't commit, don't delete.
- Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000`.
