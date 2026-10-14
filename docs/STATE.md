# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-13, Session 59

## Current milestone

**M5 (Spotlight UI) ✅ closed; next is M6 (v1 study session).** Session 59 shipped the
Spotlight page (`static/index.html`): toggles, typed Line with context-filtered suggestions,
`Ctrl+Enter`, multi-select Formations, decision labels (`XF`/`XC`/`XR`), row-click hand filter.
Built via subagent-driven development (plan: `docs/superpowers/plans/2026-10-13-spotlight-ui.md`).
Validated: 4 PT4 export diffs 0/0 (`pt4_diff.py`), 10 browser checks, and the three questions
the NL router failed (2nd barrel = `- B-?`, not `- B-B-?`). Merged and pushed (`bb9d42d`).

## Next

1. **Small fix first (TDD):** `get_hand_details` shows 9-max seat names (`MP+2`, `MP+1`,
   `UTG+1`) on 6-max hands. Join `lookup_positions` on `position` **and** `chs.cnt_players`
   (`SCHEMA_NOTES.md`, Session 59).
2. **M6:** the user runs a real study session on Spotlight instead of PT4. Note every question
   it can't answer or answers awkwardly; that list drives what comes next (M7 dashboards or fixes).

## Open questions / deferred minors

- Previous result stays visible after a toggle change until Run (filter line says what's shown).
- "1 hands" singular; a street with >8 actions says "impossible" not "unsupported".
- `pt4_diff`: whitespace-only CSV cell → spurious "missing"; wrong `--column` is a bare KeyError.

## Uncommitted work in the tree

None after this wrap-up commit. Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000`.
PT4 exports live in `exports/` (gitignored).
