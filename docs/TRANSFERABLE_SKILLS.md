# Transferable Skills Log

One AI Engineering skill per session — the thing worth applying in *any* project, not just this one. Populated automatically at the end of each session (`/wrap-up` Step 7). Entries before Session 20 are a best-effort backfill from session history (`project_poker_analytics.md`); not every early session had an explicit skill statement, so some are reconstructed rather than quoted verbatim.

---

### Session 5 (2026-07-09)
**Skill:** Validation guards should run before any expensive/external call (DB round-trip, API call), not after.
**Apply when:** code has an entry point that can be reached with bad input before touching a network/DB/disk resource — put the fail-loud check first, both for correctness and so it's testable without the real dependency.

### Session 10 (2026-07-15)
**Skill:** LLM → SQL security has three independent boundaries, each with its own mechanism: (1) whitelist lookups (dict-key checks) for anything that selects *which* code path runs, (2) hardcoded/trusted fragments for the actual SQL text, (3) parameter binding for any *value* that crosses into a query.
**Apply when:** any LLM (or other untrusted source) output is used to construct a query or command — identify which of the three boundaries each piece of output crosses, and apply the matching defense to each.

### Session 11 (2026-07-15)
**Skill:** Expected values in a test must be derived independently of the code under test (paper/hand-computed), never by running code that could share the same bug.
**Apply when:** writing any test's "ground truth" — including agent-eval ground truth, not just unit tests.

### Session 12–13 (2026-07-19)
**Skill:** A test's pass/fail criterion must be encoded explicitly and match what "success" actually means for that case — `assert` when success is a value, `pytest.raises` (or equivalent) when success IS the exception. Then: never trust a green result until you've seen it fail for the right reason (sabotage the code, confirm red, restore).
**Apply when:** any test suite, in any language/framework — the mutation-testing instinct generalizes past pytest.

### Session 14 (2026-07-20)
**Skill:** Per-tool namespaced config files (`pyproject.toml`'s `[tool.X]` sections) are a general pattern, not Python-specific — same idea as `package.json` for JS tooling.
**Apply when:** onboarding into an unfamiliar repo's tooling setup in any language.

### Session 17 (2026-07-22)
**Skill:** When a design/scope decision feels stuck ("dando vueltas en círculo"), generate evidence by simulating real usage (invent the natural-language questions a real user would ask, or adversarial cases that would break an assumed abstraction boundary) instead of debating in the abstract.
**Apply when:** an architecture-timing or scope-priority decision lacks real evidence — this is a repeatable diagnostic, not a one-off trick.

### Session 19 (2026-07-24)
**Skill:** Two faces of the same principle — treat LLM (or any external) output as untrusted input at the entry boundary, and never let an internal exception cross uncontrolled to the caller at the exit boundary.
**Apply when:** designing any system where an LLM's structured output drives real business logic and the result crosses back out to a client (API response, UI, another service).

### Session 20 (2026-07-25)
**Skill:** Validate at the shared trust boundary where multiple callers converge, not separately at each caller. Bug-triage isn't "known bug = automatic priority" — it's severity × exploitability × blocking × cost-to-fix, and sometimes the deciding factor is the boring one (low cost + already designed).
**Apply when:** more than one entry point (UI, API, CLI, batch job) calls into the same core logic — the guard belongs at the convergence point, not duplicated per caller. And: when triaging any bug, name all four axes before deciding it "obviously" goes first.

### Session 21 (2026-07-26)
**Skill:** A clean, conflict-free git merge is not evidence the merged code works — git's conflict detection is textual/line-level only, never semantic. Two non-overlapping changes across branches can combine into broken code with zero conflicts reported.
**Apply when:** merging any branch with independently-developed changes — re-run the test suite after every merge, not only after resolving conflicts, and explicitly note what the suite does *not* cover (e.g. an integration point no test touches).

### Session 22 (2026-07-27)
**Skill:** Designing a service's error boundary means separating what crosses out to the client (minimal, safe) from what stays logged internally (rich, complete) — they aren't a trade-off against each other, they're two different destinations for two different audiences.
**Apply when:** any system exposes an interface to a caller that shouldn't see internals (an API, a webhook, an agent's tool-call response) — never let internal detail leak out, but never throw it away either; log it where only you can see it.

### Session 23 (2026-07-31)
**Skill:** Testing an endpoint that depends on external services requires two things at once, not a choice between them — a real HTTP test harness (`TestClient`) so the request travels through the framework's actual dispatch (routing, middleware, error handlers), plus mocking (`monkeypatch`) so external dependencies (DB, LLM) never get hit for real. Also: when mocking an imported name, patch it where it's *used* (the importing module's namespace), not where it's *defined* — `from module import name` copies the reference at import time, so patching the original doesn't reach the copy.
**Apply when:** testing any web endpoint/handler that both calls out to external services and relies on framework-level behavior (middleware, exception handlers, auth) that only fires on the real request path — and generally, whenever mocking something reached via `from x import y`.

### Session 24 (2026-08-01)
**Skill:** Closures / function factories let you generate a family of parameterized functions from one template instead of writing near-duplicate functions per case.
**Apply when:** you catch yourself about to write several near-identical functions that differ only in one or two fixed values — a validator per rule, a handler per event type, an aggregation per metric (the same principle already behind this project's own `METRIC_CONFIGS`).

### Session 25 (2026-08-02)
**Skill:** Distinguish decorators that *register* a function (return it unchanged, just note it for later use — verifiable via `is`) from decorators that *wrap* a function (return a new function with altered behavior). This is the exact mechanism most AI agent frameworks use to expose Python functions as LLM-callable tools (`@tool`, `@function_tool`) — a registering-type decorator, same as `@app.exception_handler` or `@app.post`.
**Apply when:** reading unfamiliar code that uses decorators — from tool-calling frameworks (agent SDKs registering tools) to web frameworks (routes, error handlers) to observability wrappers (`@traceable`, `@observe`) — check whether the decorator changes the wrapped function's behavior or just annotates it for later discovery.

### Session 26 (2026-08-05)
**Skill:** Treat an inherited parent class as an API surface to inspect (`dir()`, docs, source) before assuming you need to build something yourself — not a black box. Confirmed via `pydantic.BaseModel`: `model_dump()` and a full validating `__init__` come for free, generated from the subclass's own type annotations.
**Apply when:** building on top of any framework/SDK base class you didn't write (Pydantic models, LangChain tools/agents, ORM base classes) — check what behavior you already get before writing redundant code.

### Session 27 (2026-08-07)
**Skill:** Diagnose when a test failure comes from the *testing harness's own default behavior*, not the code under test — read the traceback for where execution actually stops rather than assuming the bug is in your application logic. Confirmed via `TestClient`'s `raise_server_exceptions=True` default, which re-raises unhandled exceptions instead of routing them through the app's own registered exception handler.
**Apply when:** using any test/eval harness over a system with its own error handling (agent frameworks, API test clients, eval runners) — the harness has a policy layer of its own, separate from the app being tested, and it's worth checking before assuming a red result means your code is wrong.

### Session 28 (2026-08-08)
**Skill:** Deciding which pipeline layer a transformation belongs in should be driven by whether that layer caches or refetches on every call — not a stylistic preference between, say, SQL and pandas. Confirmed by placing `since_date_filter` post-cache in pandas for the metrics pipeline (which caches via `get_hero_df()`), while the equivalent filter for `run_filter_query` (which hits Postgres fresh every call, no cache) will need to live in SQL instead.
**Apply when:** a system has a caching layer (embeddings, an LLM call's result, a dataset fetched from an API) coexisting with a non-cached layer — the right place to filter/transform depends on which layer you're touching, not on tool preference.
