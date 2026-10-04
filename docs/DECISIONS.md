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
