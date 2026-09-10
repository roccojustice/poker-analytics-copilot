# Poker Analytics Copilot — SPEC (North Star)

*Written 2026-09-10 (Session 49). Milestone M1 output. Changes rarely — update the ladder when a milestone closes.*

## What this is

A **local web app** that replaces PokerTracker 4's *analysis* role in the user's poker
study routine. It runs alongside a solver as core study infrastructure.

Interaction: the user types a spot in poker jargon (e.g. *"frecuencias de bet en 3bp ip
pfr, bb opp"*) and gets back:

1. the **interpreted filter**, shown for confirmation
2. the **action-frequency distribution** as numbers (not charts)
3. the **list of matching hands** to inspect

It reads from PT4's Postgres DB. **PT4 stays as the importer/parser** — parsing hand
histories is out of scope. Every filter is validated by exact set membership against PT4
before it is trusted.

**Charts live only in dashboards (M6), not in the query flow.**

**"v1 done" test:** the user runs a real study session on this tool instead of PT4 and
does not fall back to PT4 for the questions it covers.

## Architecture decisions

1. **LLM selects, does not compose freely.** The LLM picks from a closed set of verified
   recipes and composes *at the layer level* — `situation` atoms that are each
   individually validated, AND-combined. Never free composition from raw atomics. The
   interpreted filter is always shown to the user.
2. **Web app over CLI** — displayed numbers + dashboards with charts are the point.
3. **PT4 is the importer.** No hand-history parsing in this project.

(Full rationale in `DECISIONS.md`.)

## The domain model

A **line** = a filter (`preflop-context` + `situation`) + the **full frequency
distribution** over the actions available at that decision point (`{bet, check}` or
`{raise, call, fold}`). Labels like *"Raise opportunity"* / *"Fold"* are views of one
distribution, not separate lines.

Three layers:

- **preflop-context** — `{2bp, 3bp} × {ip, oop} × {pfr, pfc}`. Formulas built and
  validated 0/0 against PT4 (Sessions 44/46/47), recorded in `SCHEMA_NOTES.md`.
- **situation** — the action sequence up to the decision point (`B-B`, `B-B-B`, `B-X-B`,
  `X-B-B`, `XC-X-B`, `C-B-B`, `vs Cbet`, `vs B-B`, `Flop Stab`, …). Only the subset from
  the 4 original recipes exists — building the rest is M4.
- **hero-response** — the distribution measured at the decision point.

Notation: each letter = one street. B = bet, X = check, C = call, XC = check-call.

## v1 scope — 20 lines

Ordered by the user's review priority.

### Pre-river (10)

| # | preflop-context | situation | distribution |
|---|---|---|---|
| 1 | 3bp ip pfc | faced cbet flop | raise / call / fold |
| 2 | 2bp oop pfc | faced cbet flop | raise / call / fold |
| 3 | 2bp ip pfr | bet flop | bet / check (turn) |
| 4 | 3bp oop pfr | bet flop | bet / check (turn) |
| 5 | 2bp oop pfr | bet flop | bet / check (turn) |
| 6 | 3bp ip pfc | faced cbet flop + faced barrel turn | raise / call / fold |
| 7 | 3bp ip pfr | bet flop | bet / check (turn) |
| 8 | 3bp oop pfc | faced cbet flop | raise / call / fold |
| 9 | 2bp ip pfc | faced cbet flop | raise / call / fold |
| 10 | 2bp ip pfc | IP, PFR checked flop (stab) | bet / check |

### River (10)

All measure Hero's river action: bet / check.

| # | line |
|---|---|
| 1 | 3bp oop pfr — B-B-B opportunity |
| 2 | 2bp ip pfr — B-B-B opportunity |
| 3 | 3bp oop pfr — B-X-B opportunity |
| 4 | 2bp oop pfc — XC-X-B opportunity |
| 5 | 2bp oop pfc — X-B-B opportunity |
| 6 | 2bp oop pfr — X-B-B opportunity |
| 7 | 3bp ip pfr — B-B-B opportunity |
| 8 | 3bp oop pfc — XC-X-B opportunity |
| 9 | 2bp ip pfr — X-B-B opportunity |
| 10 | 3bp ip pfc — C-B-B opportunity |

## Milestone ladder

| # | Milestone | Closes when |
|---|---|---|
| M1 | Spec written + doc-system switch | This doc exists; `STATE.md`/`DECISIONS.md` live; dead docs archived |
| M2 | Backend contract: `2bp ip pfr` B-B → validated distribution via a FastAPI endpoint, no UI | Endpoint returns `{interpreted_filter, distribution, hand_ids}` and the numbers match PT4 for that spot |
| M3 | Minimal usable UI: single-shot text query → interpreted filter + distribution (numbers) + hand list | 3–4 real questions produce usable output. **Tool is minimally usable here.** |
| M4 | Coverage: `situation` + `hero-response` registries for all 20 lines, each validated by exact set membership | The 20 lines each resolve to a verified filter |
| M5 | Conversational re-filtering: follow-up turns that extend/replace the active filter. Can start once M4 covers the pre-river lines. Session 48 already built ~80% of the plumbing. | Extend/replace by conversation works over the covered lines |
| M6 | Dashboards: one per line, 20 total. Each design defined by the user when reached. | Each line has its dashboard |
| M7 | Packaging: one command to launch, no dev shell | Runs as an app |

## Conserved from the pre-pivot codebase

- `preflop-context` formulas validated 0/0 against PT4 (`SCHEMA_NOTES.md`)
- The 3-layer grammar
- PT4 schema knowledge, `poker_cards.py`
- `db.py` (engine, `get_hand_details()`, parameter binding), `filter_recipes.py`
  (atomics + assembly, incl. `assemble_where`)
- The validation discipline (exact set membership, never count-only)

## Rebuilt / new

- **Frontend** — none exists today (CLI `while` loop). New: FastAPI backend (`api.py`
  started) + web frontend.
- **Aggregation layer** (`analytics.py`) — today only winrate/threebet/preflop_stats;
  must grow to action-frequency-by-spot.
- **`llm_parser.py` role** — from "parse and route" to "select recipe + layer, expose
  interpreted filter".
- **`situation` / `hero-response` registries** — only the 4-recipe subset exists. The
  `situation` vocabulary doubles as the poker-shorthand glossary the LLM prompt needs
  (Session 17 gap).

## Deferred / out of scope for v1

- Multiway pots (all 20 lines are HU) — parked until MW analysis is real
- `since_date` weekday-relative support (scoped, Session 32)
- `json.JSONDecodeError` safety-net decision (Session 36–37, monitoring)
- `gpt-4o-mini` non-determinism (Session 32/35) — mitigated by "interpreted filter always
  shown"; revisit model choice at M2/M3
- PEP 8 `E501` pass (needs a `[tool.ruff]` line-length decision first)
- Stake/`cash_limit` filtering, turn-position flag verification, barrel flag,
  board-texture analysis (schema gaps, Session 17)
- LLM-assisted offline recipe drafting (Session 42 option b)
- Auth, cloud, multi-user (single-user tool by design)
