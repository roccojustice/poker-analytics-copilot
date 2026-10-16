# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-15, Session 60

## Current milestone

**M7 (breakdown filters) in progress.** M6 run 1 (this session) fell back to PT4 for missing
filters, so they moved into v1 as M7 (`SPEC.md`). Shipped this session: 6-max position names
(`77d1908`), hand table rework (`8a8f3d1`: stake, hand #, bet size as % of pot in the action
cell, result in BB with win/loss colors, Result-from/to BB list filter), date range filter
(`637aacf`: From/To, inclusive, narrows hands **and** distribution). All pushed.

## M6 run 1 findings still open

- **#5 Sizing**: frequencies by the size Hero faced (e.g. XR vs small / medium / large /
  overbet) and sizing in the Line, `2bp oop pfc vs Bs?` (s, m, l, o).
- **#6 / #11 Board & runout**: board type; flush completes turn / river, turn pairs mid card.
  Pure card math on `chs.card_1..5` + `poker_cards.py` encoding.
- **#7 Hand strength** at the decision street (air, K-high, A-high, low pair…). Open: does PT4
  store strength per street, or only `id_final_hand`?
- **#4 Replay button**: deferred (`SPEC.md`).

## Next

**Design #5 (sizing) with brainstorming.** First question is the user's: bucket thresholds for
small / medium / large / overbet. Base is ready: `amt_<street>_bet_facing/made`,
`amt_pot_<street>`, and the % convention in `SCHEMA_NOTES.md` (Session 60). Sizing narrows
both hands and distribution (like dates, unlike the BB result filter).

## Open questions / deferred minors

- Previous result stays visible after a toggle change until Run (filter line says what's shown).
- "1 hands" singular; a street with >8 actions says "impossible" not "unsupported".
- `pt4_diff`: whitespace-only CSV cell → spurious "missing"; wrong `--column` is a bare KeyError.

## Uncommitted work in the tree

None after this wrap-up commit. Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000`
(no `--reload`: restart after backend changes; Ctrl+F5 after `index.html` changes).
