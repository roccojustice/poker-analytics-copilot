# State

*Overwritten every session. Single source of truth for "where are we / what's next."*

**Last updated:** 2026-11-07, Session 72

## Current milestone

**v1 done** (M6 + M7 closed: run 3 had no in-scope fallback to PT4). **M8 redefined: GTO dashboards**,
one per spot, the user's frequencies vs a bot-vs-bot GTO PT4 DB (`PT4_2026_11_07_184219`).
First dashboard `2bp ip pfr` built on branch `feat/gto-dashboard` (spec
`docs/superpowers/specs/2026-11-07-gto-dashboard-design.md`, plan `docs/superpowers/plans/2026-11-07-gto-dashboard.md`).
Page: http://localhost:8000/dashboards.html. 832 tests green; db tests: user side = hands page (8/8 lines),
GTO preflop exact. Final review done; I-1..I-6 fixed.

## Next

1. **Verify in Chrome the two JS-only review fixes:** a blanked row (Turn filter + Cbet flop) is not
   clickable; a detail error shows ← Back; picking "Top pair" under a draw pick, then clearing the
   draw, still counts all Top pair leaves.
2. **PT4 export diff on the GTO DB** (user exports from PT4, GTO DB active: BTN open, BB call, flop
   checked to Hero, Hero bets): `pt4_diff.py ... 2bp ip pfr "X" --formation "BB vs BTN" --label B`
   with `POSTGRES_DB`/`HERO_NAME` pointed at the GTO DB → 0/0. Record in `SCHEMA_NOTES.md`.
3. Merge `feat/gto-dashboard` into `main` (if not done at wrap-up), then the user studies with it.

## Open questions / deferred minors

- Replayer parked (asked in M6 runs 1 and 3): option B chosen (PT4-style HH in BB, effective stack +
  SPR per street) from `cash_hand_histories`; parser GG + PokerStars first (99%). Needs an explicit
  exception to "no HH parsing" in SPEC.
- `2bp oop pfc` dashboard blocked: GTO `Villain` bot's cards known only at showdown (55%).
- Review minors (ledger): old caches never evicted (memory + `cache/` dirs; old dir
  `cache/PT4_2026_11_07_184219-1500000` can be deleted), `_user_cache` unbounded, 10-min user reuse not
  shown on page, `cache_key` per line, `CACHE_DIR` relative to cwd, db test hard-codes 1,500,000, quotes
  not escaped in attributes, 200 cap duplicated in JS, no AbortController.
- Earlier minors still open: no JS tests (no Node); Hand # tooltip; `spikes/` hardcode `id_player = 10`;
  villain-grammar error wording; draws spec calls; `pt4_diff` stale comment.

## Uncommitted work in the tree

- **Nothing pushed (user's call, Session 72):** `main` is 4 commits ahead of `origin/main`; `feat/gto-dashboard` (16 commits on top) is local only. Push / merge next session.
- - None. **Parked, untracked on purpose:** `docs/reports.md` + `spikes/line_volume.py`. Don't commit, don't delete.
- `.env` now also needs `GTO_POSTGRES_DB` / `GTO_HERO_NAME` (added locally). After re-importing bot hands: `python gto_cache.py build`.
