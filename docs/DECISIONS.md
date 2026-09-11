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
