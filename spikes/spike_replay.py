"""SPIKE (throwaway): can PT4's per-player action strings be replayed into one ordered sequence?

Idea: PT4 stores, per player per street, a string like "XC" (check, then call). Turn order is fixed
by poker rules, so simulate the betting round: walk seats in order, each player consumes the next
char of their string when it's their turn. Self-check: every string must be fully consumed and the
replayed aggressor order must equal PT4's own str_aggressors_<street>.
"""
import sys
from pathlib import Path
from collections import Counter

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db import engine  # noqa: E402

N_HANDS = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
STREETS = ["p", "f", "t", "r"]
POS = {0: "BTN", 1: "CO", 2: "HJ", 3: "MP", 4: "UTG+1", 5: "UTG+1", 6: "UTG", 7: "UTG", 8: "BB", 9: "SB"}


def street_order(positions, street):
    non_blinds = sorted([p for p in positions if p < 8], reverse=True)
    blinds = [p for p in (9, 8) if p in positions]
    return non_blinds + blinds if street == "p" else blinds + non_blinds


def replay_street(acts, alive, street, allin):
    """acts: pos -> remaining action string. Returns (sequence, aggressor positions, ok, reason)."""
    order = [p for p in street_order(alive, street) if p in alive]
    queues = {p: list(acts.get(p, "")) for p in order}
    to_act = {p: True for p in order}
    aggressors = [8] if street == "p" and 8 in order else []
    seq = []
    guard = 0
    while any(to_act[p] for p in order if p in alive) and guard < 200:
        guard += 1
        for p in order:
            if p not in alive or not to_act[p]:
                continue
            if not queues[p]:
                if p in allin:  # all-in earlier: can't act, not an error
                    to_act[p] = False
                    continue
                return seq, aggressors, False, "string exhausted while still to act"
            a = queues[p].pop(0)
            seq.append((POS[p], a))
            to_act[p] = False
            if a == "F":
                alive.discard(p)
            elif a in "RB":
                aggressors.append(p)
                for q in order:
                    if q != p and q in alive:
                        to_act[q] = True
            if len([q for q in order if q in alive]) == 1:
                to_act = {q: False for q in order}
                break
    leftover = {POS[p]: "".join(q) for p, q in queues.items() if q}
    if leftover:
        return seq, aggressors, False, f"unconsumed {leftover}"
    return seq, aggressors, True, ""


def main():
    players = pd.read_sql(f"""
        WITH h AS (SELECT id_hand FROM cash_hand_summary ORDER BY date_played DESC LIMIT {N_HANDS})
        SELECT chps.id_hand, chps.position, (chps.enum_allin NOT IN ('N', ''))
                 AS allin,
               ap.action AS p, af.action AS f, at.action AS t, ar.action AS r
        FROM cash_hand_player_statistics chps JOIN h USING (id_hand)
        LEFT JOIN lookup_actions ap ON ap.id_action = chps.id_action_p
        LEFT JOIN lookup_actions af ON af.id_action = chps.id_action_f
        LEFT JOIN lookup_actions at ON at.id_action = chps.id_action_t
        LEFT JOIN lookup_actions ar ON ar.id_action = chps.id_action_r""", engine)
    summ = pd.read_sql(f"""
        SELECT id_hand, hand_no, str_aggressors_p AS ag_p, str_aggressors_f AS ag_f,
               str_aggressors_t AS ag_t, str_aggressors_r AS ag_r
        FROM cash_hand_summary ORDER BY date_played DESC LIMIT {N_HANDS}""", engine).set_index("id_hand")

    results, examples = Counter(), {}
    for id_hand, g in players.groupby("id_hand"):
        g = g.fillna("")
        alive = set(g.position)
        allin = set(g.position[g.allin.astype(bool)])
        verdict = "ok"
        for s in STREETS:
            acts = dict(zip(g.position, g[s]))
            if len(alive) < 2 or not any(acts.get(p) for p in alive):
                break
            seq, ag, ok, reason = replay_street(acts, alive, s, allin)
            pt4_ag = summ.at[id_hand, f"ag_{s}"] or ""
            if not ok:
                verdict = f"{s}: {reason.split(' {')[0]}"
            elif "".join(map(str, ag)) != pt4_ag:
                verdict = f"{s}: aggressor mismatch"
            if verdict != "ok":
                examples.setdefault(verdict, (summ.at[id_hand, "hand_no"], s, seq, ag, pt4_ag, reason))
                break
        results[verdict] += 1

    total = sum(results.values())
    print(f"hands replayed: {total}")
    for k, v in results.most_common():
        print(f"  {v:6d}  {v / total:6.2%}  {k}")
    print("\nfirst example per failure kind:")
    for k, ex in examples.items():
        print(f"  [{k}] hand_no={ex[0]} street={ex[1]} replayed_ag={ex[3]} pt4_ag={ex[4]!r} {ex[5]}")
        print(f"      seq={ex[2]}")


if __name__ == "__main__":
    main()
