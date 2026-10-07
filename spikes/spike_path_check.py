"""SPIKE (throwaway): does a button path select the same hands as PT4's own flags?

Path (the user's example): folds to BTN, BTN raises, SB folds, BB calls, flop: BB checks.
Hero = BTN. Oracle = PT4: Hero on BTN, flg_f_cbet_opp, opponent BB, 1 preflop raise, 2 players
on flop. Compare hand_no sets both directions.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spike_replay import POS, engine, replay_street  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 100000

players = pd.read_sql(f"""
    WITH h AS (SELECT chs.id_hand FROM cash_hand_summary chs
               JOIN cash_hand_player_statistics me ON me.id_hand = chs.id_hand AND me.id_player IN (10, 9580)
               ORDER BY chs.date_played DESC LIMIT {N})
    SELECT chps.id_hand, chps.position, chps.id_player IN (10, 9580) AS hero,
           (chps.enum_allin NOT IN ('N', '')) AS allin, ap.action AS p, af.action AS f
    FROM cash_hand_player_statistics chps JOIN h USING (id_hand)
    LEFT JOIN lookup_actions ap ON ap.id_action = chps.id_action_p
    LEFT JOIN lookup_actions af ON af.id_action = chps.id_action_f""", engine).fillna("")

by_path = set()
for id_hand, g in players.groupby("id_hand"):
    hero_pos = g.position[g.hero].iloc[0]
    if hero_pos != 0:
        continue
    alive, allin = set(g.position), set(g.position[g.allin.astype(bool)])
    pre, _, ok, _ = replay_street(dict(zip(g.position, g.p)), alive, "p", allin)
    if not ok:
        continue
    non_fold = [(p, a) for p, a in pre if a != "F"]
    if non_fold != [("BTN", "R"), ("BB", "C")] or [a for p, a in pre if p == "SB"] != ["F"]:
        continue
    flop, _, ok, _ = replay_street(dict(zip(g.position, g.f)), alive, "f", allin)
    if ok and flop[:1] == [("BB", "X")]:
        by_path.add(id_hand)

ids = list(players.id_hand.unique())
oracle = set(pd.read_sql(f"""
    SELECT me.id_hand FROM cash_hand_player_statistics me
    JOIN cash_hand_summary chs ON chs.id_hand = me.id_hand
    JOIN cash_hand_player_statistics bb ON bb.id_hand = me.id_hand AND bb.position = 8 AND bb.flg_vpip
    WHERE me.id_player IN (10, 9580) AND me.position = 0 AND me.flg_f_cbet_opp
      AND me.flg_p_first_raise AND chs.cnt_players_f = 2 AND me.cnt_p_raise = 1
      AND bb.cnt_p_raise = 0 AND me.id_hand = ANY(%(ids)s)""", engine, params={"ids": [int(i) for i in ids]}).id_hand)

print(f"hands scanned: {len(ids)}  by_path: {len(by_path)}  pt4_oracle: {len(oracle)}")
print(f"path - oracle: {len(by_path - oracle)}   oracle - path: {len(oracle - by_path)}")
for label, diff in (("path-only", by_path - oracle), ("oracle-only", oracle - by_path)):
    for h in list(diff):
        g = players[players.id_hand == h]
        print(label, h, {POS[p]: (a, b) for p, a, b in zip(g.position, g.p, g.f)})
