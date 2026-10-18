# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-10-17, Session 61

## Current milestone

**M7 (breakdown filters) in progress.** Shipped this session: **#5 bet sizing** (merged
`056b8c5`, pushed). Per-street suffix `s/m/l/o` (cuts 45 / 70 / 105% of pot at street start)
sizes the street's only bet from Hero's row; B/X decisions split `B` into `Bs/Bm/Bl/Bo` under
an overall `B`. Validated vs PT4: 0/0, and 0/1 with one justified exact-45% hand (`SCHEMA_NOTES`).
`pt4_diff --label` diffs one distribution row.

## Next

**Write the implementation plan for the facing-bet split** (writing-plans skill), from the
approved spec `docs/superpowers/specs/2026-10-17-facing-split-design.md`: sized labels
`XFs/XCm/…` on F/C/R decisions without a decision-street suffix, a new `split` key
(size rows, row-relative %), 2D table on the page. Then execute it (Native worked well).

## Still open in M7

- **#6 / #11 Board & runout**: card math on `chs.card_1..5`; needs the user's board taxonomy.
- **#7 Hand strength**: spike first — does PT4 store strength per street or only `id_final_hand`?
- Then **re-run M6** (real study session, no fallback to PT4). #4 Replay button stays deferred.

## Open questions / deferred minors

- Sizing: a NULL/zero `amt_pot_<s>` would label `Bo` (0 rows today); text reads "bet overbet".
- Previous result stays visible after a toggle change until Run; "1 hands" singular; a street
  with >8 actions says "impossible" not "unsupported".
- `pt4_diff`: whitespace-only CSV cell → spurious "missing"; wrong `--column` is a bare KeyError.

## Uncommitted work in the tree

None after this wrap-up commit. Run the app: `venv\Scripts\python -m uvicorn api:app --port 8000`
(no `--reload`: restart after backend changes; Ctrl+F5 after `index.html` changes).
