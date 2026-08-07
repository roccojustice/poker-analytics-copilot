# Backlog

Consolidated list of open threads, pending design work, and known gaps — previously scattered across `project_poker_analytics.md`'s session-by-session narrative. Updated at the end of each session (`/wrap-up` Step 7): new items added, closed items marked done (kept visible with a strikethrough + closing session, not deleted, so the log still shows real history).

## Next up (active)
- [ ] **Pick a next thread (Session 27):** with the `api.py` test backlog closed, this section has no open item. Candidates, both design-closed-not-implemented since Session 17 (see below): `date_range` support, or filter composability (`ATOMIC_FILTERS`/recipes). No pick made yet.

## Next up (closed)
- [x] ~~Tests for `api.py`, part 2 (Session 23 → 27):~~ — **closed Session 27 (2026-08-07).** Exception-handler path test (`test_handle_unexpected_exception`) shipped, committed (`dc69439`). Real bug found along the way: `TestClient` defaults to `raise_server_exceptions=True`, which re-raises unhandled exceptions instead of routing them through the app's registered exception handler — fixed with a scoped `TestClient(app, raise_server_exceptions=False)` local to this one test, not the shared module-level `client`. 11/11 tests passing.
- [x] ~~OOP primer, part 3 of 3 (Session 23 → 26):~~ — **closed Session 26 (2026-08-05).** Classes/objects, `__init__`/`self`, class vs. instance attributes, methods, and inheritance (including a real `super().__init__()` "auto-chaining" misconception, resolved live) all covered via self-written exercises and predict-then-run. Closed the `question: str` mystery from `api.py`'s `QueryRequest(BaseModel)` with a real `pydantic.ValidationError`. Closes the entire functions → decorators → OOP primer arc (Sessions 23-26). See `project_poker_analytics.md`'s Session 26 entry (Claude memory).
- [x] ~~Decorators primer, part 2 of 3 (Session 24 → 25):~~ — **closed Session 25 (2026-08-02).** Registering-type vs. wrapping-type decorators verified live via `is`; `assert` vs. `raise ValueError` corrected; 3 self-written examples (factory/poker-themed) up to a parametrized 3-level decorator, all verified predict-then-run. See `project_poker_analytics.md`'s Session 25 entry (Claude memory).
- [x] ~~Functions primer, part 1 of 3 (Session 23 → 24):~~ — **closed Session 24 (2026-08-01).** First-class functions (assign/pass/return), higher-order functions, and closures all covered via predict-then-run with real evidence. No project code touched. See `project_poker_analytics.md`'s Session 24 entry (Claude memory).
- [x] ~~Tests for `api.py` decision (Session 22):~~ — **decided Session 23 (2026-07-31).** `TestClient` (real HTTP dispatch, hits the real exception handler) + `monkeypatch` (controls `parse_user_query`/`run_query` without touching real OpenAI/Postgres) combined, not one or the other.
- [x] ~~Exception handler in `api.py` (Session 19)~~ — **closed Session 22 (2026-07-27).** Global `@app.exception_handler(Exception)` added: logs full traceback server-side (`traceback.format_exc()`), returns a minimal structured JSON error (`status_code=500`) to the client. Verified live via real sabotage (typo in `analytics.py`, confirmed 500 + traceback + clean client message, restored). Live smoke test of the `group_by` guard was inconclusive twice (LLM resisted hallucinating an invalid value both times) — not a code gap, just unverified via this specific path.
- [x] ~~Fix git branch scoping (Session 20)~~ — **closed Session 21 (2026-07-26).** `group_by` fix moved via `git stash -u` → new branch `fix/group-by-validation` off `main` → 2 atomic commits → fast-forward merge to `main` → merge commit into `fastapi-endpoint`. Both pushed, temp branch deleted.

## Design closed, not implemented
- [ ] **`date_range` support (Session 17):** label set modeled on PT4's own date-filter dropdown (`All Dates`, `Today`, `Yesterday`, `This Month`, `This Year`, `Since Date`, `Before Date`, `Between Dates`). Needs: `get_hero_hands()` SELECT to add `date_played`; a pandas-level filter applied *after* `get_hero_df()`'s cache (not a SQL WHERE, to preserve the one-fetch-per-process cache); a bound-param SQL WHERE addition for `run_filter_query` (no cache there, hits Postgres per call anyway); `llm_parser.py`/`AVAILABLE_QUERIES` updates including injecting today's date for relative-extraction cases.
- [ ] **Filter composability — atomic filters as recipes (Session 17):** `ATOMIC_FILTERS` (name → SQL fragment) + `FILTER_QUERIES` entries become `name → [atomic_names]` recipes (BOM analogy). 17-piece decomposition of the 3 existing filters already done. Two open judgment calls:
  - `pfr`/`pfc` (same flag, opposite value) — separate dict entries, or something else?
  - `total_p_raises` value variants (`=1`, `>=2`, `=2/3`) — separate atomic strings, or push toward a parametrized atomic? (Evidence from the gap-mapping exercise, gap #7, supports parametrization — 3 distinct values requested across real questions.)

## Schema/capability gaps (found via Session 17's copilot-simulation exercise, 12 gaps mapped)
- [ ] Turn-street position flag unverified — is there a `flg_t_has_position`? Never checked against real schema.
- [ ] "Barrel" concept (cbet flop + no bet turn) — no confirmed flag for Hero's own turn-betting action.
- [ ] No conversational/session state — `main.py`'s loop and `parse_user_query()` are fully stateless; a follow-up like "ahora solo los pockets" can't be interpreted. Bigger architecture gap than the rest (would make the atomic-filter-recipe design trivial to extend, once it exists).
- [ ] `run_filter_query`'s SQL skeleton never JOINs `cash_limit` — no `amt_bb` for bb-denominated filter conditions.
- [ ] Atomic filter pieces (as designed) are fixed strings — no support for user-supplied numeric thresholds (e.g. "lost 5bb or more").
- [ ] "IP"/"OOP" ambiguous without a specified street — position is tracked per-street; a bare "ip" is underspecified. `llm_parser.py` design question: repromptable? convention-based default?
- [ ] "PFC" loses precision in multi-raise (4bp+) pots — `flg_p_first_raise=false` only says "not the opener," doesn't distinguish which raise Hero called into.
- [ ] Stake/limit filtering (e.g. "200NL") — needs the same `cash_limit` JOIN as above, plus a label→`amt_bb` mapping.
- [ ] No glossary for compressed poker shorthand notation (e.g. "B-X") in `llm_parser.py`'s system prompt.
- [ ] Board-texture/hand-reading analysis (e.g. "boards BW-L-L") — doesn't exist as a capability at all; would need new combinatorial logic on top of `poker_cards.py`. Flagged as an order-of-magnitude bigger gap — out of scope for now.

## Minor / tooling debt
- [ ] `tests/test_db.py` — no test for `limit=None` path; no trailing newline at EOF.
- [ ] `pytest.approx` for float comparisons hasn't come up yet (all test data so far is binary-exact by design) — will be needed the day it isn't.
- [ ] pytest startup-time question never resolved (5.33s in an early session vs. ~0.9s later) — don't assert a cause without measuring.
- [ ] `&&` chaining behaves inconsistently in the user's Windows PowerShell 5.1 sessions — not fully diagnosed; suggest separate commands or `;` when giving PowerShell instructions.
