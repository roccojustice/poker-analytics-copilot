# Decisions

One entry per non-obvious decision: what, why, date. Append-only. Consult when something
looks settled and you don't remember why.

## 2026-09-10 (Session 49) — Goal shift: tool-use over employability

The project's primary goal changed from "AI Engineering learning vehicle / be employable"
to **"build a tool the user actually uses in his poker study routine."** Learning
continues, but the depth bar dropped — he does not need to become an expert in every
corner. Consequences: less line-by-line Socratic work, more assistant-built plumbing;
standalone primers dropped unless a specific blocker appears; the transferable-skill
ritual retired. Data-validation rigor stays (a tool he relies on must not lie).
Supersedes `user_profile.md`'s 2026-07-05 tie-breaker ("default to whatever teaches more
AI Engineering").

## 2026-09-10 (Session 49) — LLM selects, never composes freely

The NL layer picks from a closed set of verified recipes and composes only at the layer
level (individually-validated `situation` atoms, AND-combined). No free composition from
raw atomics at runtime. The interpreted filter is always displayed for confirmation.
Why: runtime composition fails silently — returns a plausible-but-wrong hand set the user
can't detect (established Sessions 42/46). The 3-layer grammar (Session 43) makes
layer-level composition safe because each layer is validated independently.

## 2026-09-10 (Session 49) — Web app over CLI

Displayed numbers + per-line dashboards with charts are core functionality; a CLI can't
serve them. Query-flow output is numbers; charts are dashboards-only (M6).

## 2026-09-10 (Session 49) — PT4 stays the importer

The tool reads PT4's Postgres DB. Parsing hand histories remains out of scope. The tool
replaces PT4's analysis / reports / filters / charts role, not its ingestion.

## 2026-09-10 (Session 49) — Doc-system rebuilt around one consumer

The session-tracking docs had exactly one real consumer: the next session's assistant at
`/start-session` (the user confirmed he never opened any of them between sessions).
Rebuilt to 4 files: `SPEC.md` (north star), `STATE.md` (overwritten each session),
`DECISIONS.md` (this file), `SCHEMA_NOTES.md` (unchanged reference). Retired to
`docs/archive/`: `SESSION_LOG.md`, `TRANSFERABLE_SKILLS.md`, `BACKLOG.md`.
`project_poker_analytics.md` narrative frozen (history preserved, not maintained).
`feedback_mentorship_style.md` compressed. `career_readiness.md` kept as a
personal-aspiration north star but removed from the per-session wrap-up check.
`/wrap-up` cut from 7 steps to 3.

## 2026-09-11 (Session 50) — Branch per milestone

Git workflow going forward: one branch per milestone (`m2-backend-contract`,
`m3-ui`, ...), merged to `main` when the milestone closes. Rejected "direct to
`main`" — it already mixed M5 groundwork into the M1 close this same session.
Rejected branch-per-slice — with no reviewer, the extra PR granularity is
overhead without a payoff; a milestone (weeks, not hours) is the smallest unit
he actually benefits from isolating.

## 2026-09-11 (Session 50) — hero-response as its own registry, SQL-aggregation over pandas

The `hero-response` layer (SPEC's action-frequency-at-decision-point) is its own module
(`hero_responses.py`), parallel to `filter_recipes.py`, not folded into `METRIC_CONFIGS`.
Distribution counts are computed via SQL aggregation (`db.run_distribution_query`) reusing
a recipe's already-validated `WHERE` clause, not by re-deriving the filter in pandas over
`get_hero_df()` — avoids two independently-maintained (and possibly diverging) filter
implementations for the same spot.

## 2026-09-11 (Session 50) — TDD required for functional changes

Any code change that modifies functionality/behavior — a new function, changed logic —
follows red→green TDD (`superpowers:test-driven-development` skill): write the test,
watch it fail against a real implementation (not just a missing-symbol import error), then
write minimal code to pass. Small edits that don't change behavior (a few-line tweak,
formatting) are exempt. Also settled during M2: a collection-time `ImportError` alone is
NOT sufficient RED — it never reaches the assertion, so it doesn't prove the test checks
the right thing; a minimal stub must exist first so RED is a real `AssertionError`.

## 2026-09-16 (Session 51) — Distribution queries fold into the filter family, not a third branch

Decided against adding a third `query_router` dispatch family for distribution queries.
Instead: a new registry `LINES` (`recipe_name -> hero_response_name`, in `lines.py`) marks
which filter recipes already have a validated distribution; `query_router.has_distribution()`
checks membership. The existing `filter` branch of `run_query()` returns the enriched shape
`{interpreted_filter, distribution, hands}` for those recipes, and the plain hand-details
table for the rest. Rejected embedding the recipe→hero-response link inside
`FILTER_RECIPES` itself — would have broken the uniform list shape `assemble_where()`/M5's
filter-chaining already depend on, and mixed a routing concern into a module whose job is
SQL-fragment assembly only. The 3 pre-pivot outcome recipes (`check_river_2bp_ip_pfr`,
`fold_to_3bet_preflop`, `fold_vs_small_cbet_2bp_oop_pfc`) stay out of `LINES` — their own
filter already fixes the flag a distribution would measure, so it'd be tautological
(100/0%), not a real line. M2's pilot endpoint (`GET /distribution/2bp_ip_pfr_turn_cbet_opp`)
retired in favor of the generic `/query`.

## 2026-09-28 (Session 52) — PT4 screenshot as the presentation target, split across M3/M4 and M6

User shared a PT4 screenshot as a rough prototype/sketch (not pixel-perfect spec — info can
be added/removed) for where the UI's presentation should land. It has two distinct parts
that map to different milestones:
- **"Hands For Stake" grid** (position, hole cards, flop/turn/river actions, winner, pot,
  BB won, rendered with colored position badges and graphical cards, not text) — this is
  the same hand-list rendering already being built into the query-flow UI (M3/M4), just
  more polished. Next concrete step when picked back up: a small JS/CSS component that
  renders `poker_cards.decode_card_id()`'s output as colored rank+suit tiles instead of
  plain text, plus position badges, on top of the existing table.
- **Aggregate stats-by-stake summary table** (top of the screenshot) — this is dashboard
  content (aggregated across the whole dataset, no single-spot filter), already parked at
  M6 by the `SPEC.md` rule "charts live only in dashboards, not the query flow." Not part
  of the current UI-polish work.

## 2026-09-28 (Session 52) — Frontend: plain HTML/JS, no framework

M3's UI needs no components, routing, or state management — a textarea, a button, and
structured tables rendered from `/query`'s JSON. Chose plain HTML/JS served by FastAPI
(`StaticFiles`, no build step) over a framework: JS/frontend is the user's known friction
point (`user_profile.md`), and M3 doesn't need what a framework buys. Framework choice
deferred to M6 (dashboards) if that milestone's needs actually require one.

## 2026-09-29 (Session 53) — hero-response generalized to N-way conditions

Moved `hero_responses.py` from `{flag_column, actions: {bool: name}}` (binary
only) to `{conditions: [(action_name, sql_condition), ...]}` (ordered,
first-match-wins priority). Needed for M4's raise/call/fold lines, which
don't fit a single boolean column. Same trust model as `ATOMIC_FILTERS`:
literal SQL fragments from an internal dict, never interpolated user data.
Priority matters: a raise that later folds/calls a re-raise still counts
as raise — Hero's actual decision at the original bet-facing point.

## 2026-09-29 (Session 53) — `3bp_ip_pfc_faced_cbet_flop` ships as a deliberate superset of PT4 (1065 vs PT4's 1063)

Live PT4 cross-check found PT4's own "faced cbet" filter silently excludes
a direct fold to an opponent's flop shove when that shove exceeds Hero's
effective stack (root-caused via a self-join, see `SCHEMA_NOTES.md`). User
decision after visually confirming both edge-case hands in PT4's replayer:
keep them visible in this tool — they're a real, if uncommon, spot he wants
to review, and PT4 hides them from him too. Not a bug to fix; expect the
same category on the other `faced_cbet_flop` lines in `SPEC.md`.

## 2026-10-01 (Session 54) — Two PT4-discrepancy categories confirmed as settled patterns, not case-by-case

Extends the Session 53 decision (`3bp_ip_pfc_faced_cbet_flop` as a deliberate superset). This
session confirmed two more categories, each seen across multiple lines, user-confirmed each
time after direct hand inspection:
- **Flop-3bet-into-turn** (`turn_cbet_opp` lines): Hero cbets the flop, faces a raise,
  3bets it, and reaches the turn with a cbet opportunity. PT4's export sometimes includes
  these, our query excludes them via `no_faced_raise_flop`. Confirmed on 2 lines
  (`2bp_oop_pfr_turn_cbet_opp`: 2 hands; `3bp_ip_pfr_turn_cbet_opp`: 1 hand).
- **Preflop-allin-runout** (`faced_cbet_flop` lines): Hero calls an all-in preflop, the hand
  runs out with zero flop action. PT4's export includes these under "faced cbet," our query
  excludes them because `flg_f_cbet_def_opp=false` (no real flop decision exists). Confirmed
  on `2bp_ip_pfc_faced_cbet_flop` (11 hands).

Both patterns are now settled: future lines of the same shape (`turn_cbet_opp` or
`faced_cbet_flop`) can expect the same kind of discrepancy without needing to re-litigate it
hand-by-hand with the user — unless a genuinely new pattern shows up.

## 2026-10-03 (Session 55) — Third settled PT4-discrepancy pattern; redundant atoms kept for layer readability

- **Turn-check-raise** (turn-facing-bet lines): PFR checks the turn, Hero bets, PFR
  check-raises (all-in). PT4's export includes these under its turn-facing filter; ours
  excludes them because `flg_t_cbet_def_opp=false`, Hero never faced a barrel. Confirmed on
  `3bp_ip_pfc_faced_barrel_turn` (8 hands, reviewed by user). Settled for future
  turn-facing-bet lines, same as the two Session 54 patterns.
- **Redundant atoms may stay when they make a recipe read as "previous line + one atom"**
  (e.g. `faced_cbet_flop` in `3bp_ip_pfc_faced_barrel_turn`, implied by `faced_cbet_turn`;
  `no_4bet_faced` in `3bp_oop_pfc_faced_cbet_flop`, mirroring the IP recipe). Redundancy is
  verified first (0 hands moved), so it's free; it matches how M5 composes extensions.
  Contrast: `total_raises=1` was removed from `2bp_*_pfr` because it added nothing to
  readability.

## 2026-10-04 (Session 56) — Routing changes are measured by a fixed eval, one variable per run

`routing_eval.py` holds the user's real study-session questions per line (never copied into
`examples`, which would make the eval measure memorization). Each prompt/description change is
a separate eval run. Two plausible `threebet` rewrites regressed or didn't help (70→66→65%) and
were reverted; without the eval they would have shipped.

## 2026-10-04 (Session 56) — No negation with the other tools' jargon in a tool description

"Never use for … cbet, barrel, B-B" in `threebet` pulled those questions *toward* `threebet`
and broke unrelated 2bp lines (B-B → `unknown`). Distinguish tools by strengthening the right
tool's description (identifier-first, decision street, its own synonyms), not by listing other
tools' keywords in the wrong one.

## 2026-10-06 (Session 57) — English-only line descriptions; eval questions never reused as examples

The user now asks in English, so `examples` and `routing_eval.py` are English. Each line's 3
examples cover different phrasings: short jargon, frequency question, hand-list request in
plain words. An eval question is never copied into `examples`, since that would make the eval
score meaningless. The polished descriptions were kept even though the eval came out 4 points
lower (74% → 70%), because that is within noise and the goal was consistency.

## 2026-10-06 (Session 57) — Checkpoint `main` before a possible direction change

The botonera idea, if adopted, reshapes M3–M5. Before deciding, M4 was fast-forwarded into
`main` and pushed, so `main` stays the working tool whatever happens next. The 9 validated
lines aren't lost under a botonera: their hand sets become the oracle for the path→SQL
translator.

## 2026-10-11 (Session 58) — Spotlight replaces the NL router as the query flow

The user ran a real study session on the NL app and called it "un desastre". Three of the 20
v1 lines asked in his own shorthand returned no hands, and some were routed to
`preflop_stats`. Decision: a SnapMDA-style selection bar (pot / position / role / formation)
plus a typed Line, compiled by a deterministic parser. No LLM in the v1 query flow. This
supersedes "LLM selects, never composes freely" (Session 49) for the query flow. The LLM
code is frozen, not deleted; NL may return as a refinement layer over a Spotlight result.

## 2026-10-11 (Session 58) — Compile Lines to action strings, not to flags or a replay table

Of three approaches, the Line compiles to `chps.id_action_f/t/r` conditions on Hero and
villain. Composing flag atoms (`flg_t_cbet_opp`…) would mean validating every new line
one by one again, which is the M4 bottleneck. A precomputed replayed-sequence table (the
Session 57 spike) only pays off for multiway. Heads-up, the action strings already determine
each street, so it's an ordinary indexed query with no load step. The 9 validated recipes
become the regression oracle (exact hand-set and distribution equality).

## 2026-10-11 (Session 58) — Line notation: letters belong to the preflop raiser

The user's design. PFR lines start with `-` and carry Hero's letters; PFC lines start with
`vs` and carry the villain's letters. `?` marks the decision, and Hero's *next* action there
is measured. An early draft measured the last written letter, and the user corrected it:
`XC-X-B` means Hero already bet, so what's measured is his response to a raise. A
counter-proposal (always Hero's letters plus a `vsB?` decision marker) was rejected as less
natural. The old SPEC shorthand (`C-B-B`, `XC-X-B`) mixed perspectives; e.g. `C-B-B` is now
`vs B-XC-X?`. For PFC + IP Hero, the villain's action on the decision street must be written,
because he acts first and `-?` would mix two distributions.

## 2026-10-11 (Session 58) — Formation = seat pair, OOP seat first

`BB vs BTN`, with Hero's seat implied by the IP/OOP toggle. A first draft ("Hero vs Villain")
was rejected by the user because it duplicated the toggle and broke down for common spots
where he is the BB. OOP-first matches SnapMDA, so there is one list for every combination.

## 2026-10-11 (Session 58) — v1 cuts: no NL refinement, no donks

NL refinement (board texture, sizing) is out until real use shows which refinements matter,
since that's the layer where the LLM failed. Donks (`D`) were designed, then cut by the user
for v1. The click-a-distribution-row filter covers "only the folds" without a backend.

## 2026-10-11 (Session 58) — Lines describing donks/leads are accepted, not rejected

"Donks out of v1" means no `D` notation, not that the parser rejects such sequences. A Line
like `- C-?` (pfr ip: the villain led the flop, Hero called) or `vs ?` (pfc oop: Hero leads
the flop) resolves to correct, exact action strings, and the interpreted filter shows them.
Rejecting them would also block legitimate PFC leads such as `vs X-C-?` (R5). The only
place a donk is filtered is the ambiguous case: pfr + Hero IP + `-?`, where `?` means "no
bet before Hero".

## 2026-10-13 (Session 59) — The Line is typed; presets are suggestions

The Line is an `<input>` with a native `<datalist>`, not a dropdown. Suggestions are the v1
presets for the current pot × position × role (2–3 per context). The user will eventually
study every Line, and a growing dropdown doesn't scale. `Ctrl+Enter` runs, because plain
`Enter` picks a datalist suggestion.

## 2026-10-13 (Session 59) — Formations are multi-select (OR, pooled)

None ticked = all hands; several = their hands pooled into one distribution. Pairs stay
OOP-first (`SB vs BB`) even though SnapMDA writes `BB vs SB` (the Session 58 entry's "matches
SnapMDA" was wrong on ordering), for consistency with the IP/OOP toggle and the validated
backend. Grouped buckets like SnapMDA's "HJ/LJ vs IP" are built by ticking their pairs.

## 2026-10-13 (Session 59) — Distribution labels carry Hero's decision-street prefix

`XF`/`XC`/`XR`, not `F`/`C`/`R`. That's how the user thinks about the spot; otherwise the
implied check is only visible in the filter text. With no prefix the label equals the action.

## 2026-10-13 (Session 59) — `/spot` rejects unknown fields (422)

A stale client sending the old `formation` key would otherwise get unfiltered hands silently.
A tool the user relies on must fail loud, not lie.

## 2026-10-15 (Session 60) — Breakdown filters move into v1 (M7); dashboards become M8

M6 run 1 fell back to PT4 for sizing, board/runout, hand strength and BB-result filters, not
for bugs. Top-level frequencies alone don't replace PT4; the study value is in breaking them
down. User's call.

## 2026-10-15 (Session 60) — Result-in-BB filters the hand list only; date filters both

The result depends on the action taken (a flop fold rarely loses > 5 BB), so filtering the
distribution by result biases it toward calls. The date doesn't depend on the action. Rule for
future filters: if the filter is an *outcome* of the measured action, it filters the list only.
User's call (option A).

## 2026-10-15 (Session 60) — Bet size = bet / pot at the start of the street, computed by us

PT4's `val_*_bet_facing_pct` divides by pot + bet, while `_made_pct` divides by pot. Using them
as-is would show a half-pot bet faced as 32%. One convention for both sides, pinned by a `db`
test (`SCHEMA_NOTES.md`, Session 60).

## 2026-10-15 (Session 60) — JOIN bugs get a `db`-marked test, not a mocked one

A mocked `read_sql` returns whatever the test says, so it passes with or without the bug.
Mocks stay the default for pandas logic in `db.py`.

## 2026-10-17 (Session 61) — Size suffix sizes the street's bet, from Hero's row

The suffix (`s`/`m`/`l`/`o`, cuts 45 / 70 / 105%) qualifies the street's only bet, whoever made it
and whatever letter it follows (`XRs` = check-raise vs a small bet). Raises are never sized. The
amount is Hero's row (`bet_made + bet_facing`), capped at Hero's stack, so a hand's bucket matches
the % in the hand table. Facing-bet 2D split deferred, high priority. User's call.

## 2026-10-17 (Session 61) — Facing-bet split: row-relative %, validated by set equality, not a PT4 export

On an F/C/R decision with no decision-street suffix, `/spot` adds a `split` (one row per size
bucket, response % within each row, so rows compare like the solver). `distribution` stays the
1D "All" row so the oracle and API keep working. No new PT4 export: the bucket SQL is already
PT4-validated, and requiring the split's `XCs` hands to equal `vs Bs?`'s `XC` hands is a stricter
check. User's call (option A).

## 2026-10-18 (Session 62) — Flop types are a filter, classified in Python, ordered by frequency

The user's 8 flop types (`board_types.py`) are a filter, not a breakdown: a selection narrows
distribution, split and hands, because frequencies and sizings change with texture. The
classification runs in Python over the PT4 card ids, not in SQL: one function serves the filter
and the `Flop type` column (they cannot disagree), and the rules are tested on all 22,100 flops
without a DB. The page orders the types from most to least common. Validated with the user's
fixtures, the exact counts, and a `db` test showing the 8 types partition a real result (PT4 has
no such categories to export). User's call.

## 2026-10-18 (Session 62) — A bad flop card id fails loudly

Every match is classified even with Flop = Any. If a flop card id is missing or outside 1–52, the
request fails (500) instead of showing an empty type, so a broken import shows up right away.
Current data has none. User's call.

## Earlier decisions (pre-pivot, still in force)

- **Position lives inside the `preflop-context` prefix**, not in `situation`
  (Session 44). PT4's ~80-filter catalog never collapses the
  `{SRP,3BP}×{IP,OOP}×{PFR,PFC}` matrix by position.
- **Bake a guard into a layer piece only if it's definitional**, not merely co-occurring
  (Session 43). E.g. `no_faced_raise_flop` → `turn_cbet_opp` yes; `heads_up` → no.
- **Squeeze / iso are their own layer**, decoupled from `pfc`/`pfr` base
  (Sessions 44–47).
- **"raise over limpers" dropped as a `pfr` layer** (Session 47) — `cnt_p_face_limpers`
  describes the opener's row, not Hero's; disproven empirically 183/183.
- **Domain aliases** (`2bp_ip_pfr`) are navigation labels; the machine model is the 3
  layers (Session 43).
- **Validation = exact set membership**, never count-only (Sessions 39–40, 46). A COUNT
  match can hide +N / −N.
- **Hero = `id_player IN (10, 9580)`**, hardcoded, single-user.
- **All SQL uses parameter binding**; never interpolate user/LLM-derived values.
- **Config-driven registries over `if/elif` chains** — extend behavior by adding a dict
  entry (`METRIC_CONFIGS`, `FILTER_RECIPES`, `AVAILABLE_QUERIES`).
