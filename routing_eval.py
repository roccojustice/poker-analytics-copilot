"""Routing eval: run each real question N times through parse_user_query, report hit %.

Usage: python routing_eval.py [query_name ...]   (no args = all cases)
"""
import sys
from collections import Counter

from llm_parser import parse_user_query

N_RUNS = 2  # temperature=0: repeats barely vary, phrasing coverage is what matters

# expected query_name -> real questions, as typed in a study session (translated to English S57)
CASES = {
    "3bp_ip_pfc_faced_cbet_flop": [
        "3BP IP PFC vs Cbet",
        "I want to see hands where I faced a cbet on the flop as 3bp ip pfc",
        "Last 50 hands of 3bp ip pfc vs cbet",
    ],
    "2bp_oop_pfc_faced_cbet_flop": [
        "2bp oop pfc vs cbet",
        "2bp oop pfc vs b",
        "Show me hands where I faced a cbet on the flop as 2bp oop pfc",
        "Last 50 hands in 2bp oop pfc vs cbet. I feel like yesterday I played this spot really "
        "badly and I want to confirm I didn't make many mistakes.",
    ],
    "2bp_ip_pfr_turn_cbet_opp": [
        "2bp ip pfr - turn cbet opportunity",
        "2bp ip pfr - B-B opportunity",
        "I want to see 2bp ip pfr hands where I have the opportunity to cbet the turn",
        "srp ip pfr - turn cbet opportunity",
        "2bp ip pfr - 2nd barrel opportunity",
        "Give me the last 50 hands of 2bp ip pfr - b-b opportunity",
    ],
    "3bp_oop_pfr_turn_cbet_opp": [
        "3bp oop pfr - turn cbet opportunity",
        "3bp oop pfr - B-B opportunity",
        "I want to see 3bp oop pfr hands where I have the opportunity to cbet the turn",
        "3bp oop pfr - 2nd barrel opportunity",
        "Give me the last 50 hands of 3bp oop pfr - b-b opportunity",
    ],
    "2bp_oop_pfr_turn_cbet_opp": [
        "2bp oop pfr - turn cbet opportunity",
        "2bp oop pfr - B-B opportunity",
        "I want to see 2bp oop pfr hands where I have the opportunity to cbet the turn",
        "2bp oop pfr - 2nd barrel opportunity",
        "Give me the last 50 hands of 2bp oop pfr - b-b opportunity",
    ],
    "3bp_ip_pfc_faced_barrel_turn": [
        "3bp ip pfc vs B-B",
        "3bp ip pfc vs 2nd barrel",
        "I want to see hands where I face a 2nd barrel on the turn as 3bp ip pfc",
        "Show me the last 50 hands where I face a cbet on the turn as 3bp ip pfc",
    ],
    "3bp_ip_pfr_turn_cbet_opp": [
        "3bp ip pfr - turn cbet opportunity",
        "3bp ip pfr - B-B opportunity",
        "I want to see 3bp ip pfr hands where I have the opportunity to cbet the turn",
        "3bp ip pfr - 2nd barrel opportunity",
        "Give me the last 50 hands of 3bp ip pfr - b-b opportunity",
    ],
    "3bp_oop_pfc_faced_cbet_flop": [
        "3bp oop pfc vs cbet",
        "3bp oop pfc vs b",
        "Show me hands where I faced a cbet on the flop as 3bp oop pfc",
        "Last 50 hands in 3bp oop pfc vs cbet. I feel like I've been playing this spot really "
        "badly lately and I want to confirm I haven't made many mistakes.",
    ],
    "2bp_ip_pfc_faced_cbet_flop": [
        "2BP IP PFC vs Cbet",
        "Show me hands where I faced a cbet ip as 2bp ip pfc",
        "I want to see hands where I faced a cbet on the flop as 2bp ip pfc",
        "Last 50 hands of 2bp ip pfc vs cbet",
        "srp ip pfc vs flop cbet",
    ],
    # regression guards (assistant-written): must still win after threebet is narrowed
    "threebet": [
        "What is my 3bet % by position",
        "3bet by position",
        "How often do I 3bet vs a CO open",
    ],
}

# underspecified on purpose (missing pot type / role): not scored, kept for the clarify design
AMBIGUOUS = [
    "Show me hands where I faced a cbet ip",
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
