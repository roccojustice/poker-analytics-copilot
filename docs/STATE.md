# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-21, Session 64

## Current milestone

**M7 (breakdown filters) in progress.** Shipped this session, merged to `main` (`81caf93`, `3298938`):
- **Hand strength, M7 #7 parts 1–2**: `hand_strength.py` labels Hero's made hand on the decision
  street's board (flop/turn/river) with the user's 16 types (incl. `4th pair`); Hero's hand counts
  only when his hole cards play. `Hand` multi-select + hand type × action breakdown table (size
  columns on B/X) + `Hand type` column. Validated vs PT4 `cash_hand_player_combinations` on every
  Hero hand: 45,971 flop / 31,229 turn / 20,280 river, 0 mismatches. Specs:
  `specs/2026-10-21-hand-strength-{flop,turn-river}-design.md`.

## Next

1. **User review in the app**: breakdown table width (B/Bs/Bm/Bl/Bo/X columns) and spot-checking
   labels hand by hand (click a type, read the hand list). Adjust presentation if needed.
2. **M7 #7 part 3: subcategories** (Flush nut/2nd/3rd…, Set, Two pair), defined one by one with
   the user. Then **part 4: draws** (Combo, FD nuts, FD, OESD, Gutshot, BDFD 2/1 cards, BDSD, No
   draw; exclusive by priority, independent of made hands; PT4 has `flg_<s>_*_draw` flags).
3. Then BB result filter, then **re-run M6**.

## Open questions / deferred minors

- Hand strength: board quads + A in hand = Ace high (assistant's call, user not asked); missing
  fixtures for SF over board flush, wheels, board trips, three pairs on the river; river hands run
  21 five-card combos (~2.6 s / 20k); `_rank5(board)` computed twice; `hand_type` raises on a
  NaN/0 hole card; disabled Turn/River keep a stale selection; hand-table row pick only on the name.
- Facing split on `- B?`: header says "% faced" but rows bucket Hero's own cbet. Decide before M6.
- Page: `[data-pick]:hover` outranks `.selected`; no automated test for the page click filter.
- `pt4_diff`: stale comment at line 26; no board/hand flags; wrong `--column` is a bare KeyError.
- Sizing: a NULL/zero `amt_pot_<s>` would label `Bo`.

## Uncommitted work in the tree

- **Parked idea, untracked on purpose:** `docs/reports.md` + `spikes/line_volume.py`. Don't commit, don't delete.
- Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000`.
