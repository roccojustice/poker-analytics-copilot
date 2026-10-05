"""Routing eval: run each real question N times through parse_user_query, report hit %.

Usage: python routing_eval.py [query_name ...]   (no args = all cases)
"""
import sys
from collections import Counter

from llm_parser import parse_user_query

N_RUNS = 2  # temperature=0: repeats barely vary, phrasing coverage is what matters

# expected query_name -> real questions, as typed in a study session
CASES = {
    "3bp_ip_pfc_faced_cbet_flop": [
        "3BP IP PFC vs Cbet",
        "Quiero ver manos donde me hicieron un cbet en el flop estando as 3bp ip pfc",
        "Últimas 50 manos de 3bp ip pfc vs cbet",
    ],
    "2bp_oop_pfc_faced_cbet_flop": [
        "2bp oop pfc vs cbet",
        "2bp oop pfc vs b",
        "Muéstrame manos donde enfrenté una cbet en el flop as 2bp oop pfc",
        "Últimas 50 manos en 2bp oop pfc vs cbet. Siento que ayer que estaba jugando jugué muy mal "
        "este spot y quiero reafirmar que no cometí muchos errores.",
    ],
    "2bp_ip_pfr_turn_cbet_opp": [
        "2bp ip pfr - turn cbet opportunity",
        "2bp ip pfr - B-B opportunity",
        "Quiero ver manos de 2bp ip pfr cuando tengo la oportunidad de hacer cbet en el turn",
        "srp ip pfr - turn cbet opportunity",
        "2bp ip pfr - 2nd barrel opportunity",
        "Dame las últimas 50 manos de 2bp ip pfr - b-b opportunity",
    ],
    "3bp_oop_pfr_turn_cbet_opp": [
        "3bp oop pfr - turn cbet opportunity",
        "3bp oop pfr - B-B opportunity",
        "Quiero ver manos de 3bp oop pfr cuando tengo la oportunidad de hacer cbet en el turn",
        "3bp oop pfr - 2nd barrel opportunity",
        "Dame las últimas 50 manos de 3bp oop pfr - b-b opportunity",
    ],
    "2bp_oop_pfr_turn_cbet_opp": [
        "2bp oop pfr - turn cbet opportunity",
        "2bp oop pfr - B-B opportunity",
        "Quiero ver manos de 2bp oop pfr cuando tengo la oportunidad de hacer cbet en el turn",
        "2bp oop pfr - 2nd barrel opportunity",
        "Dame las últimas 50 manos de 2bp oop pfr - b-b opportunity",
    ],
    "3bp_ip_pfc_faced_barrel_turn": [
        "3bp ip pfc vs B-B",
        "3bp ip pfc vs 2nd barrel",
        "Quiero ver manos donde enfrento un 2nd barrel en el turn as 3bp ip pfc",
        "Muéstrame las últimas 50 manos donde enfrento una cbet en el turn as 3bp ip pfc",
    ],
    "3bp_ip_pfr_turn_cbet_opp": [
        "3bp ip pfr - turn cbet opportunity",
        "3bp ip pfr - B-B opportunity",
        "Quiero ver manos de 3bp ip pfr cuando tengo la oportunidad de hacer cbet en el turn",
        "3bp ip pfr - 2nd barrel opportunity",
        "Dame las últimas 50 manos de 3bp ip pfr - b-b opportunity",
    ],
    "3bp_oop_pfc_faced_cbet_flop": [
        "3bp oop pfc vs cbet",
        "3bp oop pfc vs b",
        "Muéstrame manos donde enfrenté una cbet en el flop as 3bp oop pfc",
        "Últimas 50 manos en 3bp oop pfc vs cbet. Siento que últimamente estuve jugando muy mal "
        "este spot y quiero reafirmar que no he cometido muchos errores.",
    ],
    "2bp_ip_pfc_faced_cbet_flop": [
        "2BP IP PFC vs Cbet",
        "Muestrame manos donde enfrenté una cbet ip as 2bp ip pfc",
        "Quiero ver manos donde me hicieron un cbet en el flop estando as 2bp ip pfc",
        "Últimas 50 manos de 2bp ip pfc vs cbet",
        "srp ip pfc vs flop cbet",
    ],
    # regression guards (assistant-written): must still win after threebet is narrowed
    "threebet": [
        "Cuál es mi 3bet % por posición",
        "3bet por posición",
        "Con qué frecuencia hago 3bet vs open del CO",
    ],
}

# underspecified on purpose (missing pot type / role): not scored, kept for the clarify design
AMBIGUOUS = [
    "Muestrame manos donde enfrenté una cbet ip",
]


def run(names):
    total_hits = total_runs = 0
    for expected in names:
        print(f"\n== {expected}")
        for question in CASES[expected]:
            got = Counter(parse_user_query(question)["query_name"] for _ in range(N_RUNS))
            hits = got[expected]
            total_hits += hits
            total_runs += N_RUNS
            misses = {k: v for k, v in got.items() if k != expected}
            print(f"  {hits}/{N_RUNS}  {question!r}" + (f"  -> {misses}" if misses else ""))
    if total_runs:
        print(f"\nTOTAL {total_hits}/{total_runs} = {total_hits / total_runs:.0%}")


if __name__ == "__main__":
    run(sys.argv[1:] or list(CASES))
