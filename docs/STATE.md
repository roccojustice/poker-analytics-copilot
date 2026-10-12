# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-11, Session 58

## Current milestone

**M4 (Spotlight core) ✅ closed; next is M5 (Spotlight UI).** Session 58 replaced the NL
router, which failed in real use, with Spotlight: a deterministic Line parser plus `POST /spot`.
The oracle matches all 9 validated recipes exactly (hand sets and distributions). Merged into
`main`. Design: `docs/superpowers/specs/2026-10-11-spotlight-design.md`. M4 plan:
`docs/superpowers/plans/2026-10-11-spotlight-core.md`. The page at `localhost:8000` is still
the old NL UI; `/spot` is API-only until M5.

## Next

1. **M5 starts with brainstorming → plan.** The UI design is already in the spec ("Frontend").
2. First code step of M5 (deferred review minor): make `formation` tolerant (`""`/`"Any"` →
   `None`, case-insensitive), give a "write the OOP seat first" message only for a reversed pair,
   and lowercase pot/role/position.
3. Then replace `static/index.html` with the Spotlight bar: toggles, Line combobox with the 20
   presets filtered by role, Formation dropdown, result view, click-a-row hand filter.
4. M5 validation: 3 river Lines + `BB vs BTN` against PT4 exports by `hand_no`. Live numbers:
   `2bp oop pfc vs B-X-?` → 1,006 (B 594 / X 412); `2bp oop pfc vs B?` + `BB vs BTN` → 1,639.

## Open questions

- Other deferred minors: a street with more than 8 actions is reported "impossible" instead of
  "unsupported"; `measured_sql` crosses modules as a raw SQL fragment (safe today).
- `README.md` still describes the LLM architecture. Rewrite it for Spotlight?
- `origin/m4-situations` is stale at `06c30ff`. Delete or leave it.

## Uncommitted work in the tree

None. Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000`.
