# Spotlight — Design

*Session 58, 2026-10-11. Brainstormed and approved section by section with the user.*

## Problem

The NL query flow failed in real use. In a study session the user asked three of the 20 v1
lines in plain shorthand (`2bp ip pfr - b-b opportunity`, `3bp ip pfc vs cbet`,
`3bp oop pfr - b-b opportunity`). None returned the hands, and some were routed to
`preflop_stats`. Routing eval sat at 70%, and the misses followed a pattern (short pfc
phrasings), so they weren't random noise.

## Solution in one paragraph

**Spotlight** is a selection bar, modeled on SnapMDA's, that replaces free-text questions.
The user picks pot type, position, role and an optional seat formation, then types a
**Line** in a fixed shorthand. A deterministic Python parser (no LLM) turns the Line into
exact conditions on PT4's per-player action strings. The preflop part reuses the 0/0-validated
preflop-context formulas. The output is the same as before: interpreted filter, action-frequency
distribution, matching hands.

## Scope

**In v1:** `2BP`/`3BP` × `IP`/`OOP` × `PFR`/`PFC`, a Line on flop/turn/river, heads-up only,
Formations (seat pairs).

**Out of v1:** NL refinement (board texture, sizing…), donks (`D`), multiway, `LIMP`/`4BP`,
a precomputed sequence table. The LLM path (`/query`, `llm_parser.py`, recipes) is frozen,
not deleted.

## The Line notation

Letters: `X` check · `B` bet · `C` call · `R` raise · `F` fold. Streets are separated by `-`
(flop, turn, river). Case and whitespace are ignored.

### Rule 1: letters always belong to the preflop raiser (PFR)

| Hero's role | Line starts with | Letters are |
|---|---|---|
| PFR | `-` | Hero's actions |
| PFC | `vs` | the villain's actions |

Heads-up, the PFR's PT4 action string for a completed street determines the whole street:

| PFR string | Street |
|---|---|
| `B` | PFR bet, other called |
| `X` | both checked |
| `XC` | PFR checked, other bet, PFR called |
| `BC` | PFR bet, other raised, PFR called |

The parser derives the other player's string. The SQL constrains both players' strings on
every completed street.

### Rule 2: `?` marks the decision; Hero's next action is measured

`?` is required and always last. Exactly one `?` per Line.

- **`?` attached to a letter** (`B?`, `X?`): Hero's decision right after that action, on the
  same street.
- **`-?` at the start of a street:** Hero's first action on that street, with no bet before
  it. Measured set `{B, X}`. Hands where Hero faced a bet first are excluded (donks are out of
  v1).
- **PFC + Hero IP:** the villain (PFR) acts first on every street, so his action on the
  decision street must be written (`vs B-XC-X?`). `vs B-XC-?` is rejected with a message
  saying so.

**Measured set:** if Hero's decision follows a bet or raise, it is `{F, C, R}`; otherwise
`{B, X}`. Hands whose next Hero action falls outside the set (e.g. the villain only called,
so Hero never acts again) are excluded. The measured action is the next character of Hero's
action string on the decision street, so the distribution is a single `GROUP BY`.

### The 20 v1 lines in this notation

| # | SPEC line | Spotlight | Measured |
|---|---|---|---|
| P1 | 3bp ip pfc — faced cbet flop | `3bp ip pfc vs B?` | F / C / R |
| P2 | 2bp oop pfc — faced cbet flop | `2bp oop pfc vs B?` | F / C / R |
| P3 | 2bp ip pfr — bet flop, turn | `2bp ip pfr - B-?` | B / X |
| P4 | 3bp oop pfr — bet flop, turn | `3bp oop pfr - B-?` | B / X |
| P5 | 2bp oop pfr — bet flop, turn | `2bp oop pfr - B-?` | B / X |
| P6 | 3bp ip pfc — faced cbet + turn barrel | `3bp ip pfc vs B-B?` | F / C / R |
| P7 | 3bp ip pfr — bet flop, turn | `3bp ip pfr - B-?` | B / X |
| P8 | 3bp oop pfc — faced cbet flop | `3bp oop pfc vs B?` | F / C / R |
| P9 | 2bp ip pfc — faced cbet flop | `2bp ip pfc vs B?` | F / C / R |
| P10 | 2bp ip pfc — PFR checked flop (stab) | `2bp ip pfc vs X?` | B / X |
| R1 | 3bp oop pfr — B-B-B | `3bp oop pfr - B-B-?` | B / X |
| R2 | 2bp ip pfr — B-B-B | `2bp ip pfr - B-B-?` | B / X |
| R3 | 3bp oop pfr — B-X-B | `3bp oop pfr - B-X-?` | B / X |
| R4 | 2bp oop pfc — XC-X-B | `2bp oop pfc vs B-X-?` | B / X |
| R5 | 2bp oop pfc — X-B-B | `2bp oop pfc vs X-C-?` | B / X |
| R6 | 2bp oop pfr — X-B-B | `2bp oop pfr - X-B-?` | B / X |
| R7 | 3bp ip pfr — B-B-B | `3bp ip pfr - B-B-?` | B / X |
| R8 | 3bp oop pfc — XC-X-B | `3bp oop pfc vs B-X-?` | B / X |
| R9 | 2bp ip pfr — X-B-B | `2bp ip pfr - X-B-?` | B / X |
| R10 | 3bp ip pfc — C-B-B | `3bp ip pfc vs B-XC-X?` | B / X |

These 20 strings are also the Line combobox's preset list.

## Formations

An optional seat pair, written **OOP seat first** (postflop order: SB, BB, UTG … BTN), e.g.
`BB vs BTN`, `SB vs CO`. Hero's seat is implied by the `IP`/`OOP` toggle: `OOP` + `BB vs BTN`
→ Hero is BB. There is one list for every pot/role combination. The default is `Any` (no seat
condition). A pair that cannot occur in the chosen spot returns 0 hands, not an error. The
mapping from seat labels to `chps.position` codes (UTG/MP codes 2–7 in particular) is checked
against the data during implementation.

## Architecture

```
static/index.html (Spotlight bar)
  │  POST /spot {pot, position, role, line, formation}
  ▼
api.py  /spot
  ▼
line_parser.py   pure, no DB: (line, role, position) → LineSpec, or LineError
  ▼
spot_sql.py      LineSpec + preflop-context + formation → (where_sql, params)
  ▼
db.py            new query: Hero row + villain row (the other `flg_f_saw` player, HU flop)
                 + `lookup_actions` per street for both → hands + measured action
  ▼
{interpreted_filter, distribution, hands}
```

- **`line_parser.py`**: parses and validates the Line, simulates each heads-up street from
  the PFR's letters, and returns a `LineSpec`. That holds exact Hero/villain strings for
  completed streets; for the decision street, the street plus Hero's and the villain's
  prefixes; and the measured set. It raises `LineError` with a human-readable message:
  missing or misplaced `?`, unknown letter (including `D`), `vs` with PFR or `-` with PFC,
  more than 3 streets, impossible heads-up sequences (`XX`, `BB` within a street), PFC-IP
  without the villain's decision-street action.
- **`spot_sql.py`**: a `PREFLOP_CONTEXTS` registry with 8 entries (pot × position × role).
  Each entry is a list of existing `ATOMIC_FILTERS` names copied from the validated recipes'
  preflop part, plus `heads_up_flop` and position via `flg_f_has_position`. It adds the Line
  conditions and the Formation condition. All values go through parameter binding.
- **`db.py`**: one new function joining the villain row and the action strings. Hand display
  reuses `get_hand_details()`, plus a `measured_action` column.
- **`api.py`**: new `POST /spot`. `/query` stays as it is.

### API contract

Request: `{"pot": "2bp"|"3bp", "position": "ip"|"oop", "role": "pfr"|"pfc", "line": str,
"formation": str|null}`

Response 200:
`{"interpreted_filter": str, "distribution": [{"action", "hands", "pct"}], "hands": [...]}`
Each hand row includes `measured_action`.

Response 400: `{"error": "<parser message>"}`.

## Frontend

The existing `static/index.html` is replaced. It stays a single file with vanilla HTML/JS,
no framework.

- **Bar:** `[2BP|3BP]` (`LIMP`/`4BP` shown disabled) · `[OOP|IP]` · `[PFC|PFR]` ·
  `Line` combobox · `Formation` dropdown (`Any` default) · `Run`.
- **Line combobox:** the presets filtered by role (`-` lines for PFR, `vs` lines for PFC),
  plus free typing. `Run` is disabled while it's empty.
- **Result:**
  1. the interpreted filter in one readable line, e.g.
     `2BP · IP · PFR · BB vs BTN · Flop: Hero B, villain C · Turn: measuring B / X · 1,204 hands`
  2. a distribution table (action · hands · %)
  3. the hands table (existing renderer, plus the measured-action column)
- Clicking a distribution row filters the hands table to that action; clicking it again
  clears the filter. This is client-side only.
- Parser errors (400) are shown under the bar.

## Errors and edge cases

- Invalid Line, or a notation/role mismatch → 400 with the parser message, never 500.
- 0 hands → 200 with an empty distribution and "0 hands".
- All-in: an all-in player's later strings are empty, so Lines requiring later actions exclude
  those hands. Facing an all-in raise, `R` simply reads 0%.
- The spike's replay failures (straddles, 2-handed tables) don't apply. Preflop is resolved by
  flags, and the parser only reads heads-up postflop strings.
- NaN in hand details → normalized to `null` before serialization, covered by a test (the known
  `/query` NaN → 500 bug is not repeated).
- Unexpected exceptions → the existing generic 500 handler.

## Validation and tests

1. **`line_parser.py`: strict TDD, no DB.** Table-driven: all 20 Lines → expected `LineSpec`;
   every invalid case listed above → `LineError` with the expected message.
2. **`spot_sql.py`: no DB**, in the style of `test_query_router.py`. Values are bound, never
   interpolated; the right preflop-context per combination; the Formation condition appears only
   when a formation is set.
3. **Oracle: real Postgres, marker `db`** (`pytest -m db`, excluded from the default run). It
   asserts exact hand-set equality *and* the same distribution against the 9 validated recipes:

   | Recipe | Spotlight |
   |---|---|
   | `{2bp,3bp}_{ip,oop}_pfr_turn_cbet_opp` (4) | `… pfr - B-?` |
   | `{2bp,3bp}_{ip,oop}_pfc_faced_cbet_flop` (4) | `… pfc vs B?` |
   | `3bp_ip_pfc_faced_barrel_turn` | `3bp ip pfc vs B-B?` |

   A diff is investigated hand by hand, never "fixed in the test". If Spotlight turns out to
   be the correct side, the reason goes in `SCHEMA_NOTES.md` and those hands are listed in the
   test as explicit, justified exceptions.
4. **PT4 exports:** 3 river Lines + the `BB vs BTN` formation are checked against PT4 exports by
   `hand_no` set diff. The user exports; the assistant diffs.

## Done when

The oracle passes (or every diff is justified), the 4 PT4 export checks are clean, and the
UI answers the user's three failed questions with hands and distribution.
