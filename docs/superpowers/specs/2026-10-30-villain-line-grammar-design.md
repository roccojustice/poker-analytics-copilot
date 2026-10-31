# Villain Line grammar — design

*Session 68, 2026-10-30. Replaces the Line grammar of `2026-10-11-spotlight-design.md`.*

## Why

M6 run 2 fell back to PT4 for three spots the Line can't express, all with Hero PFR and IP and
the villain betting first on a street: `2bp ip pfr vs XR-B`, `3bp ip pfr vs XR-B`, `2bp ip pfr`
turn probe. The cause is `line_parser.py:121-122`: with no letters, `?` means "no bet before
Hero". Beyond the gap, the user finds the notation awkward: letters belong to the preflop raiser,
so `- B-?` means two different spots by position.

The user's own study list (100 lines, PT4 filter names) already writes every spot one way:
`Vs` + the villain's actions. This design adopts that.

## Goals

- One rule: **a Line is the villain's actions, by street; Hero decides right after the last one.**
- Every line of the user's list and every SPEC Line can be typed; the three M6 spots work.
- PT4 stays the oracle: exact set membership on the new spots.

## Non-goals

- `4bp` pots (out of v1). The user mentioned them only as where `Strat` would also apply.
- Filtering by the size of a raise.
- Multiway.

## Anti-goals

- Two grammars side by side.
- A new symbol that exists only to patch a gap. `D` is here because it reads as a donk at a glance.

## The grammar

```
Line    := ["vs"] street ("-" street){0,2}  |  ["vs"] "Strat"
street  := letters [size]
letters := villain's actions on that street: X B C R (no F, a fold ends the hand); D may replace a first B
size    := s | m | l | o
```

Whitespace and case don't matter. `vs` is optional and always shown in the interpreted filter.

**Hero's actions are implied.** Each street is matched against the legal heads-up sequences
(`SEQUENCES`) by the villain's string alone:

- A street before the last must be closed (`X` IP = both checked; `B` = Hero called).
- On the last street, the last action must be the villain's. If that leaves the street open,
  Hero decides there. If it closes the street, Hero must be OOP (he acts first next street) and
  the decision is on the next street with nothing done yet: `C` = decide on the turn.
- It's an error if Hero wouldn't act next (`XC` IP: the villain acts first on the turn; write
  his action) or if there is no street left (`C-C-C`).

The prototype found every legal combination unambiguous (1,688 IP, 3,587 OOP).

**Measured set:** `{F, C, R}` if Hero faces a bet, else `{B, X}`; as today.

**The result of parsing is the same `LineSpec`.** `spot_sql.py` doesn't change for the grammar.
`parse_line(line, role, position)` keeps its signature: `role` is needed only for `D` and `Strat`.

### `Strat`

Hero's first decision of the hand when he opens the action: **OOP PFR only**, a flop decision,
measures B / X. Error in any other context. Replaces `- ?`.

An empty Line is an error, as today.

### `D`

`D` = `B`, restricted to a real donk: the villain bets first on a street where **Hero was the
last aggressor of the previous street**, or of preflop on the flop (Hero PFR).

- Valid: `D` (2bp ip pfr), `XC-D`, `XC-Ds`, `XC-XC-D`, and `XC-D` as PFC IP (Hero bet the flop).
- Error: `XR-D` (the villain was last aggressor), `X-D` and `XC-X-D` (checked through), `D` as
  PFC IP (that's a cbet), and any `D` with Hero OOP (the villain doesn't act first).
- `B` in a donk's place is accepted and means the same. Only the first letter of a street can be
  `D`; `DC` works like `BC`.

### Sizes

The suffix is **the size of the street's first bet, whoever made it**, as `sizing.street_bet_sql`
already measures. Optional, per street; no suffix = any size on that street.

- `Rs`: Hero bet small and got raised. `XRl`: Hero bet large and got check-raised.
- `XCs-X`: Hero's small cbet was called. `XRs-Bl`: small on the flop, large on the turn.
- `Ds`, `Bs`: the villain's bet.
- A street with no bet can't be sized (`Xs`): error, as today.

On an unsized decision street facing a bet, the size split stays (`F/C/R` × size).

## Confirmed examples

User-confirmed, 2026-10-30:

| Context | Line | Meaning |
|---|---|---|
| 3bp oop pfr | `Rs` | Hero bet small on the flop, got raised; F/C/R |
| 2bp ip pfr | `XRs-B` | X, Hero small, raise, call; villain bets the turn, any size |
| 2bp ip pfr | `XRs-Bl` | Same, large turn bet |
| 2bp ip pfr | `XRl` | Hero bet large, got check-raised, whatever the raise size |
| 2bp ip pfr | `XCs-X` | Small cbet called, villain checks the turn; B/X |
| 2bp oop pfc | `Bs` | Villain bets small on the flop; F/C/R |
| 2bp oop pfc | `B` | Any size, with the size table |
| 2bp ip pfr | `D` | Flop donk |
| 2bp ip pfr | `XC-D` | Cbet called, turn donk |
| 2bp ip pfr | `XC-Ds` | Same, small donk |
| 2bp ip pfc | `XC-D` | Hero bet the flop as PFC, called; villain bets the turn |
| 2bp ip pfr | `XR-D` | Error: write `XR-B` |
| 2bp ip pfr | `X-B` | Hero checked back, turn probe; `B`, not a donk |
| 2bp ip pfc | `D` | Error: he's the PFR, that's a cbet (`B`) |

SPEC Lines in the new form: `- B-?` is `XC-X` IP and `C` OOP; `- B-B-?` is `XC-XC-X` IP and
`C-C` OOP; `- B-X-?` OOP is `C-X`; `- X-B-?` is `X-XC-X` IP and `X-C` OOP. PFC Lines drop `?`,
including the trailing `-?`: `vs B-X-?` is `B-X`.

## What changes

- **`line_parser.py`**: new tokenizer and `_resolve`; the `-` / `?` handling and the donk filter
  go. `?` is rejected with a message; `- ...` too.
- **`spotlight.py`**: `describe` shows `D` as a donk; nothing else in the flow.
- **`static/index.html`**:
  - `spot-config` presets become the user's list (below), placeholder `Line, e.g. vs XR-B`.
  - `lineStreets` must learn the decision street: when Hero is OOP and the last street's letters
    end in `C` or `X`, add one street. `Strat` is 1. Turn / River dropdowns depend on it.
  - The size table's header `Hands (% faced)` becomes `Hands (%)`: `Rs`-style Lines make Hero's
    own bet the common case (STATE open question).
- **`tests/`**: every old-form Line migrates (~190 occurrences, 12 files). The 9-recipe oracle
  must stay exact, proving the migration changed no result.
- **Docs**: `SPEC.md` (domain model, the 20 Lines, donks into v1), `CLAUDE.md`, `DECISIONS.md`.
- **Untouched**: `spikes/line_volume.py` (parked, old grammar, not imported by anything).

### Presets

Keyed `<pot> <position> <role>`; `SRP` = `2bp`. The user's list with names turned into letters
(`donk` → `D`, `turn donk` → `XC-D`, `river donk` → `XC-XC-D`, `flop X` → `X`, `Strat` stays),
plus the SPEC Lines it lacks: `C` (2bp oop pfr), `X-XC-X` (2bp ip pfr). Any legal Line can still
be typed; presets are suggestions.

## Validation

- TDD on the parser: the confirmed table as fixtures, each error with its message, all 100 list
  lines, the 20 SPEC Lines equal to their old `LineSpec`.
- `pytest -m db`: the oracle exact, before and after.
- **PT4 diffs by exact set membership**, both directions, on `2bp ip pfr XR-B`, `3bp ip pfr XR-B`,
  `2bp ip pfr X-B`, and one donk (`XC-D`). A sized check-raise (`XRs-B`) confirms that
  `street_bet_sql` reads Hero's bet when he was raised; it was only validated on calls and folds.
- Note: PT4 filters using `Raise Opportunity` drop hands where the bet covers Hero
  (`SCHEMA_NOTES.md`, "Result in BB"), so expect those as Spotlight extras.
- M6 re-run closes M7.

## Calls made by the assistant

- `?` and the old `-` start are rejected, not tolerated: `vs B?` would mean the same, but
  `vs B-X-?` wouldn't, and one grammar is the point.
- `B` accepted in a donk's place.
- `D` requires aggression on the previous street, matching PT4's donk definition (to confirm in
  the diff).
- Table header change, `lineStreets` rule, the two added presets.
- Work on a new branch off `main` after `m7-result-filter` merges.
