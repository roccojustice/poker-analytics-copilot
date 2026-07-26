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
