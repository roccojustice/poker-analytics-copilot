# Poker Analytics Copilot

A local analytics tool that replaces PokerTracker 4's analysis role in my study routine. I
pick a spot, and it gives me my action frequencies there plus the matching hands, so I can
find possible leaks.

# What did I do facing a cbet in 3BP IP as the caller?

```
POST /spot  {"pot": "3bp", "position": "ip", "role": "pfc", "line": "vs B?"}

3BP · IP · PFC · Any · Flop: villain B, measuring F / C / R · 1,065 hands
  Fold   378  (35.5%)
  Call   587  (55.1%)
  Raise  100   (9.4%)
+ the 1,065 hands, each with its measured action
```

# How a spot is selected: Spotlight

A selection bar (pot type, position, role, optional seat formation) plus a **Line** in poker
shorthand:

- Letters: `X` check · `B` bet · `C` call · `R` raise · `F` fold. Streets separated by `-`.
- Letters always belong to the **preflop raiser**: `-` lines are my actions (I'm the PFR),
  `vs` lines are the villain's (I'm the caller).
- `?` marks the decision; what gets measured is **my next action** there.

| Line | Spot | Measured |
|---|---|---|
| `2bp ip pfr - B-?` | I cbet flop and got called; turn | bet / check |
| `3bp ip pfc vs B-B?` | I called the flop cbet; villain barrels the turn | fold / call / raise |
| `2bp oop pfc vs B-X-?` | flop check-call, turn checked through; river | bet / check |

Formations narrow it to a seat pair, written OOP seat first (`BB vs BTN`); my seat follows
from the IP/OOP toggle.

# Architecture

Spot → Line parser → SQL builder → PT4 Postgres → distribution + hands

- **Line parser** (pure Python, no LLM): enumerates every legal heads-up betting sequence and
  finds the single one that matches the preflop raiser's letters. That gives both players'
  exact PT4 action strings per street. Impossible or ambiguous Lines are rejected with a clear
  message.
- **SQL builder**: combines those strings with preflop-context formulas validated against PT4.
  All values are bound parameters.
- **API**: FastAPI `POST /spot` → `{interpreted_filter, distribution, hands}`.

# Design decisions

* **Deterministic, not LLM.** An earlier version routed free-text questions through an LLM.
  It failed in real use, so selection is now fixed rules I can trust. The LLM path is frozen.
* **Validated by exact set membership.** Every filter is checked hand by hand against
  PT4 (`hand_no` set diff both ways), never by a count match, which can hide +N/−N errors.
  Spotlight matches the 9 previously validated lines exactly, and those checks run as a
  regression oracle (`pytest -m db`).
* Hand filtering is separated from hand display, so every spot reuses the same detail view.
* Config-driven registries instead of if/elif chains.
* Parameterized queries to prevent SQL injection.

# What it's not

* A strategy advisor for how to play poker.
* A hand history parser: PT4 imports and parses; this reads PT4's database.

# Status

The backend works end to end. Next is the web UI for the selection bar. Roadmap:
`docs/SPEC.md`.

# Stack

* Python
* FastAPI
* Pandas
* PostgreSQL
* SQLAlchemy
* pytest
