# PT4 Schema Notes

Empirical findings about PokerTracker 4's Postgres schema — none of this is documented by PT4 itself; all of it was reverse-engineered against real data across sessions. Consolidated here instead of buried in session narrative (`project_poker_analytics.md`). Append new findings here at the end of a session (`/wrap-up` Step 7); this file only grows on real, tested discoveries, not hypotheses.

## Connection / identity
- DB: `PT4_2026_02_19_191823`, local Postgres, `localhost:5432`.
- Hero: `id_player IN (10, 9580)` — two usernames (`RoccoJustice`, `Hero`) map to the same person. Hardcoded — this is a single-user MVP.
- Main table: `cash_hand_player_statistics` (aliased `chps` throughout the codebase).

## Sentinel values (PT4's "no data" convention)
- PT4 does **not** use SQL `NULL` for "no data" — it uses the sentinel FK value `0`. E.g. `id_final_hand=0` means Hero folded before showdown; `id_action_r=0` means the hand didn't reach the river.
- `lookup_hand_ranks` and `lookup_actions` have no row with `id=0`, so a `LEFT JOIN` legitimately returns `NULL` for the joined columns even though the raw FK column itself isn't `NULL`. `get_hand_details()` handles this via `fillna()` post-join (`"No showdown"` for hand-rank columns, `""` blank for action/street columns — matching PT4's own display convention). `hole_cards` is deliberately excluded from this fillna — Hero should always have 2 hole cards, so a `NaN` there should surface raw, not be masked.
- Split pots are **not** represented as a `NULL` `id_winner` — `player` has a real row `(id_player=0, player_name='[Split Pot]')`. The `LEFT JOIN` to `player` always matches; `winner` never goes `NaN` via this path.

## Card encoding (`poker_cards.py`)
- `card_id = suit_index*13 + rank_index + 1`, range 1–52.
- Suit order: `[c, d, h, s]` (clubs, diamonds, hearts, spades) — confirmed empirically against known hand #3443, not documented anywhere.
- Rank extraction from a `card_id`: `(card_id - 1) % 13`.
- Display uses ASCII letters (`c`/`d`/`h`/`s`), not Unicode suit symbols — Windows console (`cp1252`) can't encode `♣♦♥♠` and crashes on `print()`.

## Stakes
- `cash_limit.amt_bb` = the real stake big blind (e.g. `0.25` for 25NL). `amt_blind` was tried and rejected — it does not represent stake size.

## Position
- `lookup_positions` needs `DISTINCT ON` for position dedup across different game types (same position can appear more than once per game type otherwise).
- Position is tracked **per street**, not once per hand: `flg_f_has_position` (flop), `flg_r_has_position` (river), `flg_t_has_position` (turn) — confirmed to exist (Session 39), resolving what had been an open schema gap in `BACKLOG.md`.
- In a **heads-up** pot (`cnt_players_f = 2`), position is invariant across streets — `flg_f_has_position == flg_t_has_position == flg_r_has_position` (poker rules: with 2 players, whoever acts last on the flop acts last on every street). A recipe scoped to a HU spot can assert position **once**, on the earliest street it touches, instead of repeating it per street. In multiway pots position *can* change street to street (players fold out) — not relevant yet, no multiway spots analyzed (Session 43).

## Flags — preflop
- `flg_p_3bet_opp` / `flg_p_3bet` — had the opportunity to 3-bet / actually 3-bet, preflop.
- `flg_p_first_raise` — Hero made the first raise preflop (i.e. Hero is PFR/original raiser). `flg_p_first_raise=false` means Hero did not open — NOT the same as "Hero cold-called the open" (see `flg_p_ccall` below); also true for folds, 3-bets, squeezes, etc.
- `flg_p_ccall` — confirmed to exist in the real PT4 schema (Session 38, verified in pgAdmin; matches the public PT3 schema docs description: "cold called pre-flop... a flat call of a pre-flop raise"). Still ambiguous on its own between cold-calling the open vs. cold-calling a 3bet+ — combine with `hrt.total_p_raises = 1` (see `hand_raise_totals` below) to mean specifically "cold-called the open, single-raised pot." **Do NOT use it to mean "Hero was the preflop caller" — it excludes BB defenses (Session 46):** when Hero is in the BB and someone raises, Hero calling is a *call* but not a *cold* call (Hero already has the forced blind in), so `flg_p_ccall = false` for every BB-defend hand. PT4's own `SRP-*-PFC` preset includes BB defenses, so a `flg_p_ccall`-based filter undercounts badly. Build "Hero is the preflop caller" by exclusion instead (see the validated `2BP` formulas below).
- `flg_p_face_raise` — Hero faced a raise preflop.
- `flg_p_3bet_def_opp` — Hero faced a 3-bet preflop (same `_def_opp` convention as above). **Not a pure "faced a 3bet" flag — hypothesis, not fully confirmed (Session 46):** appears to fire `true` only when Hero *defends* a 3bet (calls it, or is the original raiser facing it), and `false` when Hero responds to a 3bet aggressively as a non-opener (cold-4bet). Origin: hand `RC4119885711` — Hero cold-4bet from the BB (open → villain 3bet → Hero 4bet), `flg_p_3bet_def_opp = false` despite Hero clearly having faced a 3bet. Consequence: `flg_p_3bet_def_opp = false` does **not** exclude a cold-4bet from a "2-bet pot" filter — use `cnt_p_raise = 0` for that.
- `flg_p_4bet_def_opp` — Hero faced a 4-bet-or-more preflop.
- `flg_vpip` — Hero voluntarily put money in the pot preflop.
- `cnt_p_face_limpers` — count of limpers Hero faced preflop, **before** Hero's own raise. Does NOT count a player who cold-calls Hero's raise after the fact (a caller between Hero's open and a later 3bet/squeeze is not a "limper") — confirmed Session 44 by finding hands where `flg_p_squeeze_def_opp=true` and `cnt_p_face_limpers=0` at the same time.
- `cnt_p_raise` — count of preflop raises **this specific player** made (not a hand-wide total — each player has their own row on `cash_hand_player_statistics`). Simpler than the pre-existing `hand_raise_totals` CTE (`hrt.total_p_raises`, a hand-wide SUM across all players) for the common case of "how many times did Hero raise" — confirmed to exist Session 44, not previously known. Candidate to replace the CTE in per-player recipe conditions (not done yet). **`cnt_p_raise = 0` is the clean anchor for "Hero was purely a caller preflop" in a PFC context (Session 46)** — it excludes the cold-4bet case that `flg_p_3bet_def_opp = false` misses. Empirically, for the `2BP` PFC contexts, `cnt_p_raise = 0` + the other exclusion conditions yields only hands with `hrt.total_p_raises = 1` (genuine single-raised pots, zero leaks).
- `flg_p_3bet` — Hero made the 3-bet (as opposed to `flg_p_3bet_def_opp`, facing one). Confirmed **true even for squeeze 3-bets** — PT4 does not track squeezing as a role distinct from 3-betting on this flag (Session 44).
- `flg_p_squeeze` / `flg_p_squeeze_opp` / `flg_p_squeeze_def_opp` — made a squeeze / had the opportunity to squeeze / faced a squeeze, preflop (same `_opp`/`_def_opp` convention as `3bet`/`4bet`). `flg_p_squeeze_def_opp` can be `true` even when Hero was the **original raiser** (not just a cold-caller) — happens when a caller gets involved between Hero's open and the 3-bet, i.e. it's still a squeeze relative to everyone left in the hand, not just relative to the caller. Confirmed Session 44 via 9 real hands where `flg_p_first_raise=true`, `cnt_p_face_limpers=0`, but `flg_p_squeeze_def_opp=true`.
- `flg_p_4bet` — Hero made a 4-bet (as opposed to `flg_p_4bet_def_opp`, facing one). Needed to exclude "Hero re-raised a squeeze instead of paying it" from a PFC-style ("paid the 3bet") filter — without it, a cold-4bet gets miscounted as "called."
- `enum_allin` / `enum_face_allin` — encode whether Hero went all-in / faced an all-in that street, with a letter per street (`p`=preflop, `f`=flop, `t`=turn, `r`=river; case may distinguish something not yet decoded — not investigated). Confirmed to exist Session 44; hands with `enum_face_allin='p'` (faced an all-in preflop) are legitimately included in PT4's normal PFC-style groupings, not a special case to exclude.

## Flags — flop
- `flg_f_cbet_def_opp` — Hero faced a continuation bet on the flop.
- `flg_f_has_position` — Hero has position on the flop (acts last).
- `flg_f_check_raise` — Hero check-raised the flop. Important for excluding false positives: since Hero acts first when OOP, the only way Hero raises while "facing a cbet" is via check-raise — `flg_f_check_raise=false` cleanly excludes "check-raised then folded to a re-raise" from a "folded to cbet" filter.
- `flg_f_fold` — Hero folded on the flop (reflects only the final action on that street).
- `val_f_bet_facing_pct` — the bet size Hero faced on the flop, as a plain percentage of pot (e.g. `43.61`), **not** a 0–1 fraction.

## Flags — turn / river
- `flg_t_check` — Hero checked the turn (confirmed via schema, same flag-per-street-action convention).
- `flg_t_has_position` — Hero has position on the turn (acts last). Same convention as `flg_f_has_position`/`flg_r_has_position`.
- `flg_t_cbet_opp` — Hero had the opportunity to continuation-bet the turn. Implies `flg_f_cbet = true`, but does **not** imply `flg_f_face_raise = false` — Session 39 claimed this held with no counterexamples, but Session 40 found 10 real counterexamples (`flg_f_cbet=true`, `flg_f_face_raise=true`, `flg_t_cbet_opp=true`, all hands where Hero cbet the flop, got raised, and 3bet the raise). Correction: `flg_t_cbet_opp` collapses only 2 conditions ("bet the flop as PFR"), not 3 — `no_faced_raise_flop` (`flg_f_face_raise = false`) must be added explicitly as its own atomic condition whenever a recipe wants to exclude flop-raise lines.
- `flg_r_check` — Hero checked the river.

## Known anomalies (resolved)
- ~~A recipe built on `flg_t_has_position` + `flg_t_cbet_opp` (`2bp_ip_pfr_turn_cbet_opp`, Session 39) returned 4123 hands vs. 4113 in a PT4-exported hand list for the same filter.~~ **Resolved Session 40:** not a PT4/GG-Poker-specific data issue (a control diagnostic against an already-shipped recipe matched PT4 100%, ruling that out) — the 10 extra hands all had `flg_f_face_raise = true` (Hero 3bet the flop), a case the recipe's WHERE clause didn't exclude. See the `flg_t_cbet_opp` correction above.

## Derived / computed in-app (not raw PT4 columns)
- Pocket pairs: PT4's own "pair" flag conflates board-paired hands (e.g. KT on T73r) with true pocket pairs (22–AA on the same board) — there is no direct flag for "started with a pocket pair." Must derive from `holecard_1`/`holecard_2` via rank extraction (see Card encoding above).
- `hand_raise_totals` — a CTE (used identically across all 3 `FILTER_QUERIES` entries) counting total preflop raises per hand, exposed as `hrt.total_p_raises`. Shared skeleton: this CTE + a fixed set of `JOIN`s is what all filter queries have in common; only the `WHERE` fragment varies (this is the empirical basis for the Rule-of-Three stress test in session 8 that confirmed the filters share only a SQL skeleton, not repeated Python logic).
- `cnt_players_f` (on `cash_hand_summary`) — number of players who saw the flop. Used with `flg_p_first_raise=false` and `hrt.total_p_raises=1` to infer "Hero is the sole preflop caller" without needing an explicit VPIP condition. **Lives only on `chs` — `chps` has no per-street player-count column (Session 46).** `chps.cnt_players` exists but means players *dealt in* preflop, a different concept. So any "heads-up flop" (`cnt_players_f = 2`) filter needs the `cash_hand_summary` JOIN; it can't be made JOIN-free. Street variants `cnt_players_t` / `cnt_players_r` are also `chs`-only.

## Dates
- `date_played` exists on **both** `cash_hand_player_statistics` (chps) and `cash_hand_summary` (chs) — referencing it unqualified in a query that joins both tables raises Postgres `AmbiguousColumn`. Must qualify (`chps.date_played`), same as any other column present on more than one joined table.
- Read into pandas via `pd.read_sql`, `date_played` comes back as `datetime64[us]` — confirmed empirically (predicted correctly before running).

## Tables joined across the project
`cash_hand_player_statistics` (chps), `cash_hand_summary` (chs), `lookup_positions`, `lookup_sites`, `cash_limit`, `lookup_hand_ranks` (joined twice: Hero's final hand + the winning hand), `lookup_actions` (joined three times: one per street), `player` (winner's display name).

`get_hand_details(id_hands, id_player)` is the one reusable function all filter-query results are rendered through; it uses `id_hand = ANY(%(id_hands)s)` (psycopg2 list → Postgres array adaptation) for the dynamic hand-id list, parameterized, never string-interpolated.

`cash_hand_summary.hand_no` — PT4's own hand identifier (matches the "Hand #" column in PT4's hand-list export/CSV), distinct from `id_hand` (this DB's internal PK). Used Session 44 to diff a candidate SQL filter's results against a real PT4 export by exact set membership (not just `COUNT(*)`) — join `cash_hand_summary` to get `hand_no`, cast both sides to `str` before comparing (the CSV loads it as a float in some cases, e.g. `2.57244E+11`).

## Validated `3BP-*-PFR/PFC` filter formulas (Session 44)
Hand-validated against PT4's real filter catalog via exact `hand_no` set membership (not just count match). All require `chps.id_player IN (10, 9580)` and `chs.cnt_players_f = 2` (heads-up flop) in addition to what's listed. Position is IP: `chps.flg_f_has_position = true`; OOP: `= false`.
- **`3bp_*_pfr`** (Hero made the 3-bet, either position): `flg_p_3bet = true` + `flg_p_3bet_opp = true` + `cnt_p_raise = 1` + `flg_p_face_raise = true` + `flg_p_4bet_def_opp = false`. Validated exact: IP 2180=2180, OOP 1912=1912. Includes squeeze 3-bets (no exclusion needed).
- **`3bp_ip_pfc`** (Hero faced and paid a 3-bet, in position): `cnt_p_raise <= 1` + `flg_p_3bet_def_opp = true` + `flg_p_4bet = false` + `flg_p_4bet_def_opp = false` + `flg_p_fold = false` + `flg_f_has_position = true`. Validated exact 1661=1661. Includes cold-callers facing a squeeze (`flg_p_first_raise` not required) and raise-over-limpers.
- **`3bp_oop_pfc`** (same, out of position) — **asymmetric with IP, confirmed real (checked PT4 for a squeeze checkbox difference between the two filters — none exists):** same conditions as `3bp_ip_pfc` PLUS `flg_p_first_raise = true` (cold-callers excluded entirely) PLUS `cnt_p_face_limpers = 0`. Validated exact 1383=1383.
- **Superseded mid-session, not yet finalized:** the two `pfc` formulas above match PT4's raw preset totals but were then deliberately redefined narrower — squeeze pulled out as its own layer via `flg_p_squeeze_def_opp = false` added explicitly (`ip_pfc` becomes 1600, no longer matches PT4's 1661 by design). Whether "raise over limpers" also gets pulled into its own layer is an open decision — see `BACKLOG.md`.

## Validated `2BP`/`SRP-*-PFR/PFC` filter formulas (Session 46)
Hand-validated against PT4's real filter catalog (`SRP-IP-PFR`, `SRP-OOP-PFR`, `SRP-IP-PFC`, `SRP-OOP-PFC` presets) via exact `hand_no` set membership (0 extra / 0 missing, not just count match). All require `chps.id_player IN (10, 9580)` and `chs.cnt_players_f = 2` (heads-up flop) in addition to what's listed. Position is IP: `chps.flg_f_has_position = true`; OOP: `= false`. `2BP` = 2-bet pot = `SRP` = single-raised pot (same thing; `total_p_raises = 1`).
- **`2bp_*_pfr`** (Hero opened, single-raised pot, both positions validated): `flg_p_first_raise = true` + `cnt_p_face_limpers = 0` + `flg_p_face_raise = false`. That's the whole filter. Validated exact: IP 11654=11654, OOP 5096=5096. `flg_p_3bet = false`, `flg_p_squeeze_opp = false`, `flg_p_fold = false`, `cnt_p_raise = 1` were all tried and **proven redundant** (removing them moved zero hands) — redundant under `flg_p_first_raise = true` + `flg_p_face_raise = false`.
- **`2bp_*_pfc`** (Hero was the preflop caller, single-raised pot, both positions validated): `flg_vpip = true` + `flg_p_first_raise = false` + `flg_p_3bet = false` + `cnt_p_raise = 0` + `flg_p_face_raise = true` + `flg_p_fold = false` + `flg_p_3bet_def_opp = false`. Validated exact: IP 2569=2569, OOP 6731=6731. `cnt_p_raise = 0` is load-bearing — without it hand `RC4119885711` (Hero cold-4bet from the BB) leaks in as a false positive; `flg_p_3bet_def_opp = false` alone does not catch it. Built by exclusion because no positive "preflop caller" flag exists that includes BB defenses (see `flg_p_ccall` above). No `no-limpers` condition — raise-over-limpers layering for `2BP` PFC not yet decided.
