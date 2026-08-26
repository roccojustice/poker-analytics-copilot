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

## Flags — preflop
- `flg_p_3bet_opp` / `flg_p_3bet` — had the opportunity to 3-bet / actually 3-bet, preflop.
- `flg_p_first_raise` — Hero made the first raise preflop (i.e. Hero is PFR/original raiser). `flg_p_first_raise=false` means Hero did not open — NOT the same as "Hero cold-called the open" (see `flg_p_ccall` below); also true for folds, 3-bets, squeezes, etc.
- `flg_p_ccall` — confirmed to exist in the real PT4 schema (Session 38, verified in pgAdmin; matches the public PT3 schema docs description: "cold called pre-flop... a flat call of a pre-flop raise"). Still ambiguous on its own between cold-calling the open vs. cold-calling a 3bet+ — combine with `hrt.total_p_raises = 1` (see `hand_raise_totals` below) to mean specifically "cold-called the open, single-raised pot."
- `flg_p_face_raise` — Hero faced a raise preflop.
- `flg_p_3bet_def_opp` — Hero faced a 3-bet preflop (same `_def_opp` convention as above).
- `flg_p_4bet_def_opp` — Hero faced a 4-bet-or-more preflop.
- `flg_vpip` — Hero voluntarily put money in the pot preflop.
- `cnt_p_face_limpers` — count of limpers Hero faced preflop.

## Flags — flop
- `flg_f_cbet_def_opp` — Hero faced a continuation bet on the flop.
- `flg_f_has_position` — Hero has position on the flop (acts last).
- `flg_f_check_raise` — Hero check-raised the flop. Important for excluding false positives: since Hero acts first when OOP, the only way Hero raises while "facing a cbet" is via check-raise — `flg_f_check_raise=false` cleanly excludes "check-raised then folded to a re-raise" from a "folded to cbet" filter.
- `flg_f_fold` — Hero folded on the flop (reflects only the final action on that street).
- `val_f_bet_facing_pct` — the bet size Hero faced on the flop, as a plain percentage of pot (e.g. `43.61`), **not** a 0–1 fraction.

## Flags — turn / river
- `flg_t_check` — Hero checked the turn (confirmed via schema, same flag-per-street-action convention).
- `flg_t_has_position` — Hero has position on the turn (acts last). Same convention as `flg_f_has_position`/`flg_r_has_position`.
- `flg_t_cbet_opp` — Hero had the opportunity to continuation-bet the turn. Empirically confirmed (Session 39, no counterexamples found in real data) to imply both `flg_f_cbet = true` and `flg_f_face_raise = false` — i.e. this single flag already encodes "bet the flop as PFR and the bet wasn't raised," collapsing what would otherwise be 3 separate atomic conditions into one.
- `flg_r_check` — Hero checked the river.

## Known anomalies (unresolved)
- A recipe built on `flg_t_has_position` + `flg_t_cbet_opp` (`2bp_ip_pfr_turn_cbet_opp`, Session 39) returned 4123 hands vs. 4113 in a PT4-exported hand list for the same filter — a strict superset, 10 extra hands, all on **GG Poker**, all with `hand_no` starting `RC` or `HD` (most GG Poker hand numbers in this DB are plain numeric — these are not). Cause not yet identified; see `BACKLOG.md` for the open investigation and next diagnostic step.

## Derived / computed in-app (not raw PT4 columns)
- Pocket pairs: PT4's own "pair" flag conflates board-paired hands (e.g. KT on T73r) with true pocket pairs (22–AA on the same board) — there is no direct flag for "started with a pocket pair." Must derive from `holecard_1`/`holecard_2` via rank extraction (see Card encoding above).
- `hand_raise_totals` — a CTE (used identically across all 3 `FILTER_QUERIES` entries) counting total preflop raises per hand, exposed as `hrt.total_p_raises`. Shared skeleton: this CTE + a fixed set of `JOIN`s is what all filter queries have in common; only the `WHERE` fragment varies (this is the empirical basis for the Rule-of-Three stress test in session 8 that confirmed the filters share only a SQL skeleton, not repeated Python logic).
- `cnt_players_f` (on `cash_hand_summary`) — number of players who saw the flop. Used with `flg_p_first_raise=false` and `hrt.total_p_raises=1` to infer "Hero is the sole preflop caller" without needing an explicit VPIP condition.

## Dates
- `date_played` exists on **both** `cash_hand_player_statistics` (chps) and `cash_hand_summary` (chs) — referencing it unqualified in a query that joins both tables raises Postgres `AmbiguousColumn`. Must qualify (`chps.date_played`), same as any other column present on more than one joined table.
- Read into pandas via `pd.read_sql`, `date_played` comes back as `datetime64[us]` — confirmed empirically (predicted correctly before running).

## Tables joined across the project
`cash_hand_player_statistics` (chps), `cash_hand_summary` (chs), `lookup_positions`, `lookup_sites`, `cash_limit`, `lookup_hand_ranks` (joined twice: Hero's final hand + the winning hand), `lookup_actions` (joined three times: one per street), `player` (winner's display name).

`get_hand_details(id_hands, id_player)` is the one reusable function all filter-query results are rendered through; it uses `id_hand = ANY(%(id_hands)s)` (psycopg2 list → Postgres array adaptation) for the dynamic hand-id list, parameterized, never string-interpolated.
