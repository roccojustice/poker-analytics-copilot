# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-15, Session 60

## Current milestone

**M6 run 1 done; v1 did not pass yet. Next is M7 (breakdown filters).** Session 60 fixed the
6-max position names in `get_hand_details` (`77d1908`, join on `position` + `cnt_players`), then
the user ran a real study session on Spotlight. No bugs found. He fell back to PT4 for the
missing breakdown filters (#5, #6, #7, #10, #11 below), not for the replayer. Scope changed:
those filters moved into v1 as M7 (`SPEC.md`); dashboards are now M8, packaging M9.

## M6 run 1 findings (user's words, grouped)

**A. Hand table (display only, cheap)**
1. Show the stake of each hand (`cash_limit` is already joined).
2. Bet sizes as % of pot, not USD/BB (needs the pot at the start of each street; check schema).
3. Hide `id_hand` and `measured_action`.
8. More descriptive column names.
9. Color rows: won vs lost.

**B. Breakdown filters (M7)**
10. Filter by BB won/lost at the end of the hand ("I always review pots where I lost > 5 BB").
5. Frequencies by sizing (e.g. XR vs small / medium / large) and sizing in the Line:
   `2bp oop pfc vs Bs?` (s small, m medium, l large, o overbet).
6. Filter by board type.
11. Runout filters: flush closes turn, flush closes river, turn pairs mid card, etc.
    Computable from `chs.card_1..5` + `poker_cards.py` encoding, no PT4 flag needed.
7. Filter by hand strength (air, K-high, A-high, low pair…) to see what I fold / check / raise.
   Open: does PT4 store strength per street, or only `id_final_hand`?

**C. Out of scope for now**
4. Replay button per row (PT4's replayer can't be opened from a browser; own replayer = big).

## Next

1. **Group A + #10** in one session: quick display wins plus the easiest filter.
2. **M7 proper:** pick the first breakdown filter. Sizing (#5) fits the Line grammar most
   naturally; runout (#11) is pure card math. Design each before coding (brainstorming).

## Open questions / deferred minors

- Sizing buckets: thresholds for small / medium / large / overbet are the user's call.
- `tests/test_db.py` now has a `db`-marked test (position names): a mock can't catch a JOIN bug.
  Note in `DECISIONS.md` at wrap-up.
- Previous result stays visible after a toggle change until Run (filter line says what's shown).
- "1 hands" singular; a street with >8 actions says "impossible" not "unsupported".
- `pt4_diff`: whitespace-only CSV cell → spurious "missing"; wrong `--column` is a bare KeyError.

## Uncommitted work in the tree

`docs/SPEC.md` (scope change, ladder) and `docs/STATE.md` (this file). `77d1908` not pushed.
Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000`. PT4 exports live in
`exports/` (gitignored).
