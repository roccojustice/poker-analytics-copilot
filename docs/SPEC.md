# Poker Analytics Copilot — SPEC (North Star)

*Written 2026-09-10 (Session 49). Rewritten 2026-10-11 (Session 58) for the Spotlight
direction. Changes rarely; update the ladder when a milestone closes.*

## What this is

A **local web app** that replaces PokerTracker 4's *analysis* role in the user's poker
study routine. It runs alongside a solver as core study infrastructure.

Interaction is **Spotlight**, a selection bar modeled on SnapMDA's. The user picks pot type,
position, role and optional seat formations, then types a **Line** in poker shorthand
(e.g. `3bp ip pfc vs B?`). The app returns:

1. the **interpreted filter**, in one readable line
2. the **action-frequency distribution** as numbers (not charts)
3. the **list of matching hands** to inspect

It reads from PT4's Postgres DB. **PT4 stays as the importer/parser.** Parsing hand
histories is out of scope. Every filter mechanism is validated by exact set membership
against PT4 before it is trusted.

**Charts live only in dashboards, not in the query flow.**

**"v1 done" test:** the user runs a real study session on this tool instead of PT4 and
does not fall back to PT4 for the questions it covers.

Full design: `docs/superpowers/specs/2026-10-11-spotlight-design.md`.

## Architecture decisions

1. **Deterministic selection, no LLM in the v1 query flow.** The bar plus a parsed Line
   map to SQL through fixed rules. The free-text LLM router failed in real use (Session 58).
   It is frozen, not deleted; NL may come back later as a *refinement* over a Spotlight
   result.
2. **The Line compiles to PT4's per-player action strings** (`chps.id_action_f/t/r`).
   The preflop part reuses the preflop-context formulas validated 0/0 against PT4.
3. **Web app over CLI.** Displayed numbers and dashboards are the point.
4. **PT4 is the importer.** No hand-history parsing in this project.

(Rationale in `DECISIONS.md`.)

## The domain model

A **line** = a filter (`preflop-context` + `situation`) + the **full frequency
distribution** of Hero's next action at the decision point (`{B, X}` or `{F, C, R}`).

Three layers, mapped onto the Spotlight bar:

- **preflop-context**: `{2bp, 3bp} × {ip, oop} × {pfr, pfc}`, from the bar's toggles.
  Formulas are in `SCHEMA_NOTES.md`.
- **situation**: the Line. Letters always belong to the preflop raiser: PFR lines start with
  `-` (Hero's letters), PFC lines with `vs` (the villain's letters). `?` marks the decision.
- **hero-response**: Hero's next action at the `?`, measured from his action string.

Plus optional **formations** (seat pairs, OOP seat first, e.g. `BB vs BTN`), multi-select:
none = all hands, several = their hands pooled.

## v1 scope: 20 lines

Ordered by the user's review priority. They are also the Line input's suggestions.

### Pre-river (10)

| # | preflop-context | Line | Measured |
|---|---|---|---|
| 1 | 3bp ip pfc | `vs B?` | F / C / R |
| 2 | 2bp oop pfc | `vs B?` | F / C / R |
| 3 | 2bp ip pfr | `- B-?` | B / X |
| 4 | 3bp oop pfr | `- B-?` | B / X |
| 5 | 2bp oop pfr | `- B-?` | B / X |
| 6 | 3bp ip pfc | `vs B-B?` | F / C / R |
| 7 | 3bp ip pfr | `- B-?` | B / X |
| 8 | 3bp oop pfc | `vs B?` | F / C / R |
| 9 | 2bp ip pfc | `vs B?` | F / C / R |
| 10 | 2bp ip pfc | `vs X?` | B / X |

### River (10)

| # | preflop-context | Line | Measured |
|---|---|---|---|
| 1 | 3bp oop pfr | `- B-B-?` | B / X |
| 2 | 2bp ip pfr | `- B-B-?` | B / X |
| 3 | 3bp oop pfr | `- B-X-?` | B / X |
| 4 | 2bp oop pfc | `vs B-X-?` | B / X |
| 5 | 2bp oop pfc | `vs X-C-?` | B / X |
| 6 | 2bp oop pfr | `- X-B-?` | B / X |
| 7 | 3bp ip pfr | `- B-B-?` | B / X |
| 8 | 3bp oop pfc | `vs B-X-?` | B / X |
| 9 | 2bp ip pfr | `- X-B-?` | B / X |
| 10 | 3bp ip pfc | `vs B-XC-X?` | B / X |

### Breakdown filters (added Session 60, from the first M6 run)

The first real study session fell back to PT4 for these. Each narrows any Line's result
and its distribution:

- **Bet sizing** of the bet Hero faces or makes (small / medium / large / overbet), in the
  Line (`vs Bs?`) and as a per-sizing distribution
- **Board / runout**: flop texture, flush completes on turn/river, turn pairs a flop card,
  etc. Computed from the card ids (`poker_cards.py` encoding), not from PT4 flags
- **Hand strength** at the decision street (air, K-high, A-high, low pair, …)
- **Result in BB** (e.g. lost more than 5 BB); narrows the hand list only, not the distribution
- **Date range** (From / To, inclusive); narrows both. Shipped Session 60

## Milestone ladder

| # | Milestone | Status / closes when |
|---|---|---|
| M1 | Spec written + doc-system switch | ✅ Session 49 |
| M2 | Backend contract: one validated distribution via FastAPI | ✅ Session 50 |
| M3 | Minimal usable UI (NL text query) | ✅ Session 52. Failed in real use (Session 58); superseded by M5 |
| M4 | **Spotlight core:** `line_parser.py` + `spot_sql.py` + `POST /spot` | ✅ Session 58. Oracle 9/9 exact (hand sets + distributions), no exceptions |
| M5 | **Spotlight UI:** bar, Line input, Formations, result view | ✅ Session 59. 4 PT4 export diffs 0/0; the three failed questions answered in the UI |
| M6 | v1 study session | Run 1 (Session 60): fell back to PT4 for missing breakdown filters. Re-run after M7 |
| M7 | **Breakdown filters**: sizing, board/runout, hand strength, BB result | Each validated against PT4 by exact set membership; M6 re-run passes |
| M8 | Dashboards: one per line, 20 total. Each design defined by the user when reached | Each line has its dashboard |
| M9 | Packaging: one command to launch, no dev shell | Runs as an app |

## Conserved from earlier work

- `preflop-context` formulas validated 0/0 against PT4 (`SCHEMA_NOTES.md`)
- The 3-layer grammar
- PT4 schema knowledge, `poker_cards.py`
- `db.py` (engine, `get_hand_details()`, parameter binding), `filter_recipes.py` atomics
- The 9 validated recipes, now the **regression oracle** for Spotlight
- The validation discipline (exact set membership, never count-only)

## Frozen (kept, not extended)

- `llm_parser.py`, `queries.py`, `query_router.py`, `POST /query`, `routing_eval.py`,
  `lines.py` / `hero_responses.py`, and the metric queries in `analytics.py`

## Deferred / out of scope for v1

- NL refinement over a Spotlight result ("only the folds" beyond the client-side click
  filter); board texture and bet sizing moved into v1 as breakdown filters (Session 60)
- Donk notation (`D`); PT4 has `flg_<street>_donk*` flags to validate it against
- Multiway, `LIMP` / `4BP`, and a precomputed replayed-sequence table (needed for multiway;
  feasibility shown in the Session 57 spike, `spikes/`)
- Stake/`cash_limit` filtering (schema gap, Session 17; showing the stake per hand is in scope)
- In-app hand replayer (asked for in M6 run 1; a project of its own)
- PEP 8 `E501` pass (needs a `[tool.ruff]` line-length decision first)
- Auth, cloud, multi-user (single-user tool by design)
