# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-11, Session 58

## Current milestone

**M4 (Spotlight core) closed in Session 58; next is M5 (Spotlight UI).** The NL app failed in
real use, so Session 58 replaced it with Spotlight: design in
`docs/superpowers/specs/2026-10-11-spotlight-design.md`, plan in
`docs/superpowers/plans/2026-10-11-spotlight-core.md`. `POST /spot` works end to end. The
oracle matches all 9 validated recipes exactly (hand sets and distributions) on the first run.
The user's three failed questions now return hands and distribution live. Merged into `main`
(local, not pushed). The page is still the old NL UI; `/spot` is API-only until M5.

## Next

1. Push `main` to `origin` when the user decides (13 commits ahead).
2. **M5, first:** make `formation` tolerant: `""`/`"Any"` → `None`, case-insensitive, and say "write the OOP seat first" only for a reversed pair (deferred review minor). Also lowercase pot/role/position.
3. **M5:** replace `static/index.html` with the Spotlight bar (spec, "Frontend" section):
   toggles, Line combobox with the 20 presets filtered by role, Formation dropdown, result
   view, click-a-row hand filter.
4. M5 validation: 3 river Lines + `BB vs BTN` against PT4 exports by `hand_no`. The user
   exports, the assistant diffs. Live numbers to compare against: `2bp oop pfc vs B-X-?` →
   1,006 hands (B 594 / X 412); `2bp oop pfc vs B?` + `BB vs BTN` → 1,639 hands.

## Open questions

- `origin/m4-situations` is stale at `06c30ff` (all of it is in `main`). Delete or leave it.

## Uncommitted work in the tree

None. Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000` →
http://localhost:8000 (the page is still the NL UI; `/spot` is API-only until M5).
