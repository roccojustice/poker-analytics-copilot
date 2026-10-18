# Facing-bet split — Design

*Session 61, 2026-10-17. Brainstormed and approved with the user. Builds on
`2026-10-17-sizing-design.md` (buckets, street's-bet formula, sized labels).*

## Problem

To see how Hero responds to each bet size today, the user runs the same Line four times
(`vs Bs?`, `vs Bm?`, `vs Bl?`, `vs Bo?`). That comparison comes up often in study sessions, so
it was deferred with high priority when sizing shipped.

## Solution in one paragraph

When the decision measures a response to a bet (`F` / `C` / `R`) and the decision street has
**no size suffix**, `/spot` also returns a **split**: one row per size bucket, each with the
response frequencies **within that row**. The page shows it as a 2D table under an "All" row
(the distribution as it is today).

## When it applies

- Decision measured `F` / `C` / `R` **and** the decision street has no suffix → split.
- Decision street has a suffix (`vs Bs?`) → no split; labels stay unsized, as today.
- Decision measured `B` / `X` → unchanged (the Hero-bet split from the sizing spec).
- The size is the decision street's only bet, as everywhere (`street_bet_sql`). On a decision
  facing a raise (`- B?`: Hero cbet, villain raised) rows group by **Hero's cbet size**, the
  same thing `- Bs?` filters today.

## Labels

The SQL appends the size to the measured letter: `F` → `Fs`, `Cm`, `Rl`, `Ro`, … Spotlight
prefixes as today, so hands carry `XFs`, `XCm`, … — the user's own notation from the Line
(`XCs` = check-call vs a small bet). Same bound `Decimal` thresholds as the Hero-bet label.

## `/spot` response

- `distribution` is **unchanged**: the F / C / R rows over all hands (the table's "All" row).
  The oracle and existing API consumers keep working.
- New key `split`, `null` when it doesn't apply, else a list in bucket order, zero rows
  included:

```json
[
  {"size": "S", "name": "small", "hands": 2136, "pct_faced": 80.1,
   "cells": [
     {"action": "F", "label": "XFs", "hands": 837, "pct": 39.2},
     {"action": "C", "label": "XCs", "hands": 1003, "pct": 47.0},
     {"action": "R", "label": "XRs", "hands": 296, "pct": 13.9}
   ]},
  {"size": "M", "name": "medium", "...": "..."}
]
```

- `pct_faced` = row hands / all hands. Cell `pct` = cell hands / row hands (each row sums to
  100%; a zero row has every `pct` at 0.0).

## Page

```
Size     Hands (% faced)   XF      XC      XR
All      2,668  (100%)     39.0%   47.0%   14.0%
small    2,136  (80.1%)    39.2%   47.0%   13.9%
medium     312  (11.7%)    …
large      198   (7.4%)    …
overbet     22   (0.8%)    …
```

- Each cell shows the % with the hand count small underneath.
- Click a **cell** → hands of that size and action. Click a **row name** → every hand of that
  size. Click an **All** cell → that action across all sizes. Click again to clear, as today.
- Without a split the page renders the 1D distribution exactly as today.

## Testing

TDD, red then green.

- `spot_sql`: a facing decision without suffix returns a sized measured expression
  (`'F'`/`'C'`/`'R'` + size); with a decision suffix it stays the bare letter; the WHERE still
  filters on the letter.
- `spotlight` (mocked DB): `split` order, `pct_faced`, row-relative `pct`, zero rows, `null`
  when not applicable; `distribution` unchanged (sized labels collapse back to F / C / R).
- `db`-marked:
  - split cells sum to the 1D distribution, cell by cell;
  - for every size and action, the hands labelled e.g. `XCs` on `vs B?` are **exactly** the
    `XC` hands of `vs Bs?` (set equality).
- The existing oracle stays green (it collapses labels to their first letter).

## Validation

No new PT4 export. The bucket is the same SQL already validated against PT4 (sizing spec,
`SCHEMA_NOTES.md` Session 61), and the set equality against the suffixed Lines is a stricter
check than an export.

## Out of scope

- A split on a decision street that already has a suffix.
- Raise sizing (raises are never sized).
