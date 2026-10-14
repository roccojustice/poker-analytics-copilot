# Spotlight — Design

*Session 58, 2026-10-11. Brainstormed and approved section by section with the user.
Frontend, API contract and errors revised in Session 59 (2026-10-13) for M5.*

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

These 20 strings are also the Line input's suggestions.

## Formations

A seat pair, written **OOP seat first** (postflop order: SB, BB, UTG … BTN), e.g.
`BB vs BTN`, `SB vs CO`. Hero's seat is implied by the `IP`/`OOP` toggle: `OOP` + `BB vs BTN`
→ Hero is BB. There is one list for every pot/role combination.

**Formations are multi-select.** None selected = every hand of the spot (no seat condition).
One or more selected = the hands of *any* of them (OR), pooled into one distribution. Example,
`2bp oop pfc vs B?`: `BB vs BTN` 1,639 hands, `BB vs CO` 1,029, both → 2,668. Grouped buckets
(e.g. SnapMDA's "HJ/LJ vs IP" = `UTG vs MP/CO/BTN` + `MP vs CO/BTN`) are covered by ticking their
pairs; a one-click group shortcut is out of M5. A pair that cannot occur in the chosen spot
contributes 0 hands, not an error. Seats use
PT4's 6-max labels and codes: `SB` 9, `BB` 8, `UTG` 3, `MP` 2, `CO` 1, `BTN` 0 (15 pairs).
Codes 4–7 only occur at 7+ handed tables (~1% of Hero's hands); they appear under `Any` but in
no formation.

## Architecture

```
static/index.html (Spotlight bar)
  │  POST /spot {pot, position, role, line, formations}
  ▼
api.py  /spot
  ▼
line_parser.py   pure, no DB: (line, role, position) → LineSpec, or SpotInputError
  ▼
spot_sql.py      LineSpec + preflop-context + formations → (where_sql, params)
  ▼
db.py            new query: Hero row + villain row (the other `flg_f_saw` player, HU flop)
                 + `lookup_actions` per street for both → hands + measured action
  ▼
{interpreted_filter, distribution, hands}
```

- **`line_parser.py`**: parses and validates the Line, simulates each heads-up street from
  the PFR's letters, and returns a `LineSpec`. That holds exact Hero/villain strings for
  completed streets; for the decision street, the street plus Hero's and the villain's
  prefixes; and the measured set. It raises `SpotInputError` (shared with `spot_sql.py` for bad bar values) with a human-readable message:
  missing or misplaced `?`, unknown letter (including `D`), `vs` with PFR or `-` with PFC,
  more than 3 streets, impossible heads-up sequences (`XX`, `BB` within a street), PFC-IP
  without the villain's decision-street action.
- **`spot_sql.py`**: a `PREFLOP_CONTEXTS` registry keyed by pot × role (4 entries; position is added via `ip_flop`/`oop_flop`).
  Each entry is a list of existing `ATOMIC_FILTERS` names copied from the validated recipes'
  preflop part, plus `heads_up_flop` and position via `flg_f_has_position`. It adds the Line
  conditions and the Formation condition: `(Hero seat, villain seat) IN (...)` over the selected
  pairs. All values go through parameter binding.
- **`db.py`**: one new function joining the villain row and the action strings. Hand display
  reuses `get_hand_details()`, plus a `measured_action` column.
- **`spotlight.py`**: orchestrates parse → SQL → query → distribution → hand details, and
  builds the interpreted-filter text.
- **`api.py`**: new `POST /spot`. `/query` stays as it is.

### API contract

Request: `{"pot": "2bp"|"3bp", "position": "ip"|"oop", "role": "pfr"|"pfc", "line": str,
"formations": [str]}`

- `pot`, `position` and `role` are case-insensitive.
- `formations` defaults to `[]` (no seat condition). Each entry must be one of the 15 pairs
  exactly as listed; duplicates are ignored.

Response 200:
`{"interpreted_filter": str, "distribution": [{"action", "label", "name", "hands", "pct"}],
"hands": [...]}`

- `label` is Hero's prefix on the decision street plus the measured action, e.g. `XF` / `XC` /
  `XR` for `2bp oop pfc vs B?` (Hero's implied check + the response to the bet). With no prefix
  it equals `action` (`B` / `X`).
- The interpreted filter's "measuring …" part uses the labels too.
- Each hand row includes `measured_action`, holding the same label as the distribution row it
  counts toward, so the client-side row filter matches by string equality.

Response 400: `{"error": "<parser message>"}`.

## Frontend

The existing `static/index.html` is replaced. It stays a single file with vanilla HTML/JS,
no framework.

- **Bar:** `[2BP|3BP]` (`LIMP`/`4BP` shown disabled) · `[OOP|IP]` · `[PFC|PFR]` ·
  `Line` input · `Formations` multi-select · `Run`.
- **Line input: typing is the primary path.** A plain `<input>` with a native `<datalist>` of
  suggestions. The suggestions are the v1 presets **for the current pot × position × role**
  (2–3 per context), so the list never grows as more Lines get studied. Any Line can be typed.
- **Run:** the button, or `Ctrl+Enter` in the bar. Plain `Enter` does not run, because the
  browser uses it to pick a datalist suggestion. `Run` is disabled while the Line is empty.
- **Formations multi-select:** a dropdown panel with one checkbox per pair (15, OOP seat
  first, all enabled). Closed, it shows the selected pairs, or `Any` when none is ticked. Picking
  from a fixed list means a formation can't be mistyped.
- The 20 presets and the 15 formations are hardcoded in `index.html`. A formation list that
  drifts from `spot_sql.FORMATIONS` fails loud (400), not silently.
- **Result:**
  1. the interpreted filter in one readable line, e.g.
     `2BP · OOP · PFC · BB vs BTN, BB vs CO · Flop: Hero X, villain B, measuring XF / XC / XR · 2,668 hands`
  2. a distribution table (label · hands · %)
  3. the hands table (existing card/table renderer, plus the `measured_action` column), with
     every row and no pagination
- Clicking a distribution row filters the hands table to that label; clicking it again
  clears the filter. This is client-side only.
- Parser errors (400) are shown directly under the Line input; a 500 shows the existing
  generic message.
- **Out of M5:** a UI for `/query` (the endpoint stays, with no page), a recent-Lines
  history, column sorting.

## Errors and edge cases

- Invalid Line, or a notation/role mismatch → 400 with the parser message, never 500.
- Unknown formation → 400 naming it. The UI can't send one; this guards direct API calls and
  a drifted hardcoded list.
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
   every invalid case listed above → `SpotInputError` with the expected message.
2. **`spot_sql.py`: no DB**, in the style of `test_query_router.py`. Values are bound, never
   interpolated; the right preflop-context per combination; the Formation condition appears only
   when at least one formation is selected, and binds every selected pair.
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
