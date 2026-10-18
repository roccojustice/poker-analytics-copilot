# Bet sizing (M7 #5) — Design

*Session 61, 2026-10-17. Brainstormed and approved with the user.*

## Problem

M6 run 1 fell back to PT4 for sizing: frequencies split by the size of the bet Hero faced
(e.g. XR vs a small bet) and Hero's own bet-size frequencies. Spotlight has no notion of size.

## Solution in one paragraph

An optional **size suffix** (`s` / `m` / `l` / `o`) at the end of any street's letters in the
Line filters on the size of **that street's bet**. When the decision measures Hero's own
bet (`B` / `X`), the distribution splits `B` into one row per size bucket, under an overall
`B` row.

## Buckets

Size = **the street's bet / pot at the start of that street** (`amt_pot_<street>`), the
convention already used for the hand table (DECISIONS, Session 60). Lower bound inclusive,
upper exclusive:

| Suffix | Name | Range |
|---|---|---|
| `s` | small | `[0, 45%)` |
| `m` | medium | `[45%, 70%)` |
| `l` | large | `[70%, 105%)` |
| `o` | overbet | `[105%, ∞)` |

Defined once, in a `SIZE_BUCKETS` registry.

## The Line

- The suffix goes **at the end of a street's letters**, at most one per street:
  `vs Bs-XCl-?`, `- XRs?`, `vs Bm?`.
- It sizes **the only bet of that street**. Heads-up, a street has at most one bet; every
  later aggression is a raise. Raises are never sized.
- Who made the bet doesn't matter, and the letter it follows doesn't matter:

| Line | Reads | The suffix sizes |
|---|---|---|
| `vs Bs?` | villain cbets small; Hero decides | villain's cbet |
| `vs XCs-?` | villain checks, Hero bets small, villain calls | Hero's bet |
| `- XRs?` (Hero PFR OOP) | Hero checks, villain bets small, Hero raises, … | villain's bet |
| `vs BCl-?` | villain bets large, Hero raises, villain calls | villain's bet, not Hero's raise |

- The decision street takes a suffix too (`vs Bs?`): it sizes the bet Hero faces there.
- **Errors** (`SpotInputError` → 400): a suffix on a street whose resolved sequence has no bet
  (`- Xs-?`, `vs Xs?`); more than one suffix on a street; a suffix anywhere but the end of the
  street's letters.
- A Line without suffixes behaves exactly as today. The 9-recipe oracle is unchanged.

## SQL

- The street's bet = `chps.amt_<s>_bet_made + v.amt_<s>_bet_made` (Hero's row + the villain
  row `run_spot_query` already joins; exactly one is non-zero when the street has a bet).
  **Pin with a `db` test before relying on it.**
- Per suffixed street: `bet >= %(lo)s * chs.amt_pot_<s> AND bet < %(hi)s * chs.amt_pot_<s>`
  (no upper condition for `o`). Multiplying instead of dividing keeps exact boundaries (a bet
  of exactly 45% is `m`) free of rounding. `lo` / `hi` are bound params.
- `build_spot_query` reads the sizes from the `LineSpec` (one optional size per street).

## Distribution (Hero's bet split)

When the decision measures `B` / `X`, `measured_action` for a bet carries its bucket
(`Bs`, `Bm`, `Bl`, `Bo`), computed in SQL from Hero's `amt_<s>_bet_made` on the decision street.
Rows, in this order:

```
B      38%   overall
  Bs   15%
  Bm   12%
  Bl    9%
  Bo    2%
X      62%
```

- Sub-rows are **% of all hands** (Bs + Bm + Bl + Bo = B), the solver's convention.
- Each sub-row carries `"parent": "B"` so the page indents it; zero rows included, as today.
- The decision-street prefix applies as today (`X` + `B` → `XB`, `XBs`, …).
- Measured `F` / `C` / `R` (Hero facing a bet) is not split.

## Hand table and interpreted filter

- Each hand's `measured_action` is the sized label (`Bs`, …). Clicking `B` shows every bet;
  clicking `Bs` shows only small ones (prefix match on the overall row).
- The interpreted filter names the size: `Flop: Hero X, villain B small (<45%)`.
- The Line field gets a one-line hint listing the suffixes.

## Testing

TDD, red then green:

- `parse_line`: suffix per street, decision-street suffix, every error above, no-suffix Lines
  unchanged.
- `build_spot_query`: one bound `lo`/`hi` pair per suffixed street, none without suffixes,
  no `hi` for `o`.
- `run_spot` (mocked DB): split rows, order, overall row, parents, labels, zero rows.
- `db`-marked: the street's-bet formula against known hands; the existing oracle unchanged.
- `tests/test_static_config.py` keeps presets valid.

## Validation against PT4

Exact set membership with `pt4_diff`, on two Lines: one with a faced-bet suffix (e.g.
`2bp oop pfc vs Bs?`) and one Hero-bet split row (e.g. `Bs` on `2bp ip pfr - ?`).

PT4's faced-bet % divides by pot **+ bet**, so our thresholds convert as `p / (1 + p)`:
45% → **31.03%**, 70% → **41.18%**, 105% → **51.22%**. PT4's made-bet % divides by pot and
needs no conversion. Boundary diffs from PT4's rounding are explained hand by hand, not forced.

## Deferred

- **Facing-bet split** (high priority, the user uses it often): with no suffix on the decision
  street and Hero facing a bet, a 2D table of size faced (S/M/L/OB) × F/C/R. Today it takes one
  run per suffix.
- Raise sizing.
