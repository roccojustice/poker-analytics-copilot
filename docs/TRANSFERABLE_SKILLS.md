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

### Session 29 (2026-08-09)
**Skill:** Distinguish loud bugs (crash/syntax error — self-reporting, cheap to catch) from silent bugs (run clean, produce wrong output — only caught by active verification) when building queries, prompts, or configs dynamically. Confirmed via two real bugs in the same `run_filter_query()` edit: a misplaced `ORDER BY` clause (loud — invalid SQL, errored immediately) versus an unconditional `since_date` WHERE addition (silent — would have run fine and silently over-filtered the 3 existing filters whenever called without `since_date`, the default/normal case).
**Apply when:** any code assembles a query, prompt, or config conditionally from pieces — "it ran without error" is not proof of correctness for the silent-bug class; verify against an independent source of truth (a paper calculation, a second tool, a known-good baseline) rather than trusting a clean run.

### Session 30 (2026-08-10)
**Skill:** Prioritize what to test first by the real cost of a bug going undetected, not by the order code was built — and within that, weigh both severity (how bad if wrong) and silence (how likely to go unnoticed). A loud bug self-reports; a silent bug in decision-critical logic (this project's `since_date`, feeding real poker decisions) is the combination that most urgently needs a test written first.
**Apply when:** triaging a test-coverage backlog in any system where errors can propagate silently and feed real decisions — data pipelines, an agent's tool-call outputs, evals that measure the wrong thing without failing, financial calculations. Triage by "what's the blast radius if this is silently wrong," not "what did I just build."

### Session 31 (2026-08-15)
**Skill:** Don't delegate deterministic tasks to the LLM — specify them in code instead. Confirmed via two `since_date` bugs in the same prompt: a literal example date (`"2023-01-01"`) got copied verbatim into real output instead of being computed from an explicit "Today is X" instruction, and even after fixing that plus adding an explicit "use today's date as reference" instruction, compound relative-date arithmetic ("November last year") still produced a fabricated year with zero change from the fix — proving the failure was model capability, not prompt wording.
**Apply when:** any subtask inside an LLM prompt has a single objectively-correct, code-verifiable answer (arithmetic, date math, counting, exact formatting) — resolve it deterministically in code and restrict the LLM to natural-language understanding (intent, routing, extraction), not computation.

### Session 32 (2026-08-16)
**Skill:** A task that looks non-deterministic end-to-end can actually be a bundle of a genuine natural-language-understanding step plus a deterministic computation step — decompose it before deciding whether it goes to the LLM or to code, instead of judging the whole task as one atomic unit. Confirmed by redesigning `since_date`: resolving "since november last year" isn't one fuzzy task, it's "identify which components the user named" (LLM) plus "compute the resulting date" (Python `relativedelta`) — splitting it that way is what actually fixed the Session 31 bug.
**Apply when:** an LLM handles something that "feels" fuzzy end-to-end (extraction + computation, parsing + validation, summarization + counting) — agentic tool calling, RAG pipelines with numeric/date filters, structured extraction feeding downstream business logic. Look for the seam between "understanding what was asked" and "computing the answer" before assigning the whole task to one side.

### Session 33 (2026-08-17)
**Skill:** Mock a nested method on an already-instantiated third-party SDK object (not a wrapper function you wrote) by reconstructing its response shape with small classes, when the real SDK returns attribute-chained objects instead of plain dicts.
**Apply when:** testing code that calls a third-party client/SDK directly (`client.chat.completions.create(...)`, a vector-DB client, any object with `.attribute.attribute` access on its return value) — a plain dict or `unittest.mock.Mock` return value won't satisfy dot-notation access the same way a small purpose-built class does, and `monkeypatch.setattr` can target the nested method path directly on the real instantiated object.

### Session 34 (2026-08-18)
**Skill:** Seeing a test go red isn't sufficient evidence a sabotage or predicted bug was caught — the failure's specific cause (error type, message, value) has to match what you predicted, since an unrelated bug can produce a red test that looks like confirmation but isn't testing what you think it is.
**Apply when:** running sabotage-verification or predict-then-run on any test suite — before accepting a red result as proof, compare the actual failure (exception type, assertion message, diffed value) against your prediction, not just its pass/fail state. Same discipline applies to CI failures and bug-repro steps: a red pipeline confirms *something* broke, not that it broke for the reason you think.

### Session 35 (2026-08-19)
**Skill:** JSON Schema (and structured tool-calling in general) guarantees the *shape* of an LLM's output — types, required fields, structure — but not its *meaning*. The semantics of each field (sign conventions, units, relative vs. absolute, when it applies) still has to be conveyed in text: property `description`s, examples, well-chosen names. Confirmed live: a `since_date.years` field typed `integer` with no `description` made `gpt-4o-mini` return an absolute year (`2022`) instead of the intended signed relative offset (`-1`) — fixed by adding an explicit `description` to each property.
**Apply when:** designing any structured-output contract for an LLM (OpenAI/Anthropic tool calling, function calling, structured outputs, a Pydantic response schema) — type the fields for validity, but explicitly document the convention for anything not self-evident from the field name alone. A schema that validates cleanly can still carry a semantically wrong value.

### Session 36 (2026-08-21)
**Skill:** A schema property's `type` guarantees shape and validity, not meaning — confirmed a second time (after Session 35's `since_date.years`) on `limit`: with no `description`, the same ambiguous question ("algunas manos...") resolved inconsistently across live runs (sometimes `limit: 10`, sometimes `limit` omitted entirely, i.e. unlimited). Fixed with an explicit `description` telling the model to omit the field rather than guess a number for vague phrasing; reverified 4/4 consistent afterward.
**Apply when:** any LLM-facing schema property has more than one plausible interpretation under ambiguous natural-language input — don't assume a passing smoke test on an unambiguous phrasing means the field is safe; stress-test with a real ambiguous phrase and run it multiple times before deciding whether a `description` is actually needed.

### Session 37 (2026-08-23)
**Skill:** Design the state's shape and semantics — what operations it needs to support, what information it must represent — before deciding where or how it's stored. Confirmed while designing v2 conversational filter composability: naming the 3 possible behaviors (accumulate/reset/clarify) and what data each needs came first; only then did "local variable vs. module-level global" become a quick, low-cost decision. A wrong storage location is cheap to fix later; a wrong state model forces redesigning everything built on top of it.
**Apply when:** designing any stateful system — a database schema, an agent's session/conversation state, a cache — decide the model (operations + shape) before the mechanism (where it lives, what technology holds it).

### Session 38 (2026-08-24)
**Skill:** Distinguish executing a function immediately from deferring its execution by storing the data needed to call it later, at the moment you actually have the right context for the result. Confirmed via a real bug caught twice building a parametrized atomic filter: `ATOMIC_FILTERS["total_raises"]('=', '1')` genuinely called the function, but at dict-definition time — before an assembly function existed to receive the result and pair it with a `params` entry — silently losing the real value into a placeholder name. Fixed by storing `("total_raises", "=", 1)` as inert data (a tuple), deferring the actual call until the piece that knows what to do with the result exists.
**Apply when:** a function's inputs are known before the context needed to use its output is ready — callbacks, factories, deferred/lazy evaluation, any "recipe" or config defined in one place and executed in another. The bug is easy to miss because it doesn't crash — it just silently produces the wrong thing at the wrong time.

### Session 39 (2026-08-26)
**Skill:** Verify against reality in two independent layers, not one — automated tests catch "did I break behavior I already trusted," while comparison against an external ground truth (a live system, a second implementation, a trusted export) catches "is this new behavior actually correct, not just plausible." Neither layer substitutes for the other: today's `pytest` run caught a broken cross-file import that no PT4 comparison would ever surface, while a PT4-export diff caught a 10-hand data discrepancy that a fully green test suite said nothing about. When a discrepancy against ground truth appears, its *magnitude* is itself evidence — a small deviation (10 of 4123) points to an edge case, not a broad logic error.
**Apply when:** any code transforms, filters, or aggregates data sourced from something external (an API, a database, a legacy system) — pair a regression-test layer (protects already-trusted behavior) with an independent ground-truth comparison (validates new behavior), and read the size of any mismatch as a clue to its cause before chasing it.

### Session 41 (2026-08-30)
**Skill:** The syntax used to add a field to a dict (inside the literal vs. assigned after construction) should mirror whether that field is universal or conditional — not be arbitrary. Confirmed by finding a real inconsistency in an LLM tool-calling schema: an unconditional field (`action`) had been added via post-hoc assignment, the idiom this codebase reserves for conditional fields (`group_by`/`limit`, each behind an `if`) — it belonged in the literal dict next to the other unconditional field (`since_date`).
**Apply when:** building any config dict, API payload, or schema with a mix of always-present and conditionally-present fields — let the code's structure communicate which fields are universal vs. conditional, so a reader doesn't have to trace logic to know.

### Session 42 (2026-08-31)
**Skill:** Distinguish *selection* from *synthesis* when designing an LLM's role in a system. An LLM is reliable at selecting from a closed set of pre-verified options — worst case it picks wrong and you see it immediately. It is unreliable at synthesizing a new artifact from primitives when the spec carries implicit conditions or domain knowledge it doesn't have — and that failure is silent: a plausible-but-wrong output you can't catch without checking against ground truth. Confirmed by contrasting `queries.py` (LLM picks one pre-verified tool — works) against a proposed design where the LLM composes SQL filter recipes at runtime from atomic-piece descriptions (fails: a required condition like "didn't face a flop raise" is part of the spot's meaning to a domain expert, isn't in the user's phrasing, and can't be written into a piece's description without turning it into a recipe).
**Apply when:** you're about to let an LLM *build* something (a query, a config, a multi-step plan) rather than *choose* among options you already validated — first ask where the knowledge that makes the output correct actually lives, and whether you can verify the result before trusting it.

### Session 43 (2026-09-01)
**Skill:** Discover a complex domain's latent grammar by re-expressing already-verified artifacts, then cut the pieces at boundaries that make them both composable *and* verifiable-once. Don't design the grammar top-down — force existing verified instances (here: 4 hand-built, PT4-checked filter recipes + a real ~80-item filter list) into a mold and see what structure resists; that's the same Rule-of-Three discipline applied to finding structure. Choose piece boundaries so each piece can be checked against ground truth once and reused, not re-verified per combination — using "is this condition *definitional* of the piece, or does it merely *co-occur*?" to place the cut (definitional → bake it in; co-occurring → separate piece).
**Apply when:** an LLM has to assemble something structured from natural language — tool schemas, query builders, config, a DSL — and you need each piece to be checkable against the truth before you trust the composition.

### Session 46 (2026-09-07)
**Skill:** When you define a category by *exclusion* (enumerating what it is NOT) rather than by a positive attribute the source system already provides, you cannot verify your exclusion list is complete by reading it — you do not know what case you forgot. Only an exhaustive diff against ground truth surfaces the missing case, and it does more than pass/fail: the discrepant record *names* the condition you are missing (here: hand RC4119885711, a cold-4bet from the BB, revealed the filter needed `cnt_p_raise = 0`). Set-membership verification stops being a gate and becomes the tool that finishes building the definition. Contrast a positive-flag definition (`flg_p_3bet = true`), where the source system already carries the completeness guarantee.
**Apply when:** you are classifying or filtering data with compound rules you authored yourself (not a pre-given flag) — eval-set inclusion criteria, routing rules, cohorts defined by a combination of conditions. Count matches lie and visual inspection cannot prove completeness; diff the full set against an independent ground truth and read each discrepancy as a pointer to the rule you left out.

### Session 47 (2026-09-08)
**Skill:** Context engineering / memory tiering — decide what information lives permanently in active context versus what gets archived and retrieved on demand, and always leave an explicit pointer to the archived content. Confirmed by pruning this project's own oversized Claude-memory file (Sessions 1-34 moved to a separate, not-auto-loaded archive): the risk this creates isn't data loss (nothing is deleted), it's *retrieval recall failure* — the same named problem RAG systems face — a future lookup not thinking to check the archive. The fix isn't just doing the split correctly; it's adding a standing instruction to check the archive before concluding something isn't known.
**Apply when:** any LLM-based system accumulates more history/state than fits (or should fit) comfortably in one context window — agent memory, RAG document stores, a system prompt that grows over time, log/documentation management with an LLM in the loop. Splitting hot from cold storage is only half the job; the pointer from hot to cold is what prevents silent information loss in practice.

### Session 48 (2026-09-09)
**Skill:** Treat an untested branch as a latent silent failure, and encode a verified behavior as a test *immediately* after verifying it — because the cost isn't writing the test, it's the re-comprehension tax you pay coming back to code that has drifted out of your head. The mechanical trigger: after writing or changing code, ask "if I inverted the core logic of what I just wrote, would an existing test go red?" — if no, write one now, before moving on. This session a signature change (`db.run_filter_query`) left `query_router.run_query`'s filter branch silently calling the old contract with *zero* test exercising that path — caught only by manually reasoning through the call graph, not by a red test. Separately: constrain an LLM's output structurally, not with prose — the `action` field was moved off metric tool schemas entirely so `action` + a metric query becomes an unrepresentable state rather than a discouraged one.
**Apply when:** code evolves in layers and a change to one layer's contract (a signature, a return shape) can silently break a caller nothing exercises; or you're relying on an instruction in a prompt/description to stop an LLM emitting a field it shouldn't — prefer removing the field from that schema.
