AVAILABLE_QUERIES = {
    "winrate": {
        "group_by_options": ["position", "site"],
        "description": "Calculate Hero's BB/100 grouped by any dimension.",
        "examples": [
            "Calculate my winrate by position",
            "What position wins the most?",
            "What is my winrate in BB?",
        ],
    },
    "threebet": {
        "group_by_options": ["position"],
        "description": (
            "Calculate Hero's 3Bet percentage grouped by position. "
            "Use this when the user asks about 3Bet, re-raising preflop, "
            "raising after another player opened the pot, or raise frequency versus an open."
        ),
        "examples": [
            "Calculate my 3Bet percentage by position",
            "What position has the highest 3Bet percentage?",
            "What is my 3Bet percentage when someone opens the pot?",
            "What is my raise frequency versus an open raise?",
        ],
    },
    "preflop_stats": {
        "group_by_options": ["position"],
        "description": (
            "Calculate Hero's preflop stats grouped by position. "
            "Use this when the user asks about VPIP or PFR, "
            "putting money into the pot or open raise from any position"
        ),
        "examples": [
            "Calculate my vpip & pfr by position",
            "How much do I raise preflop from the button?",
            "How much do I vpip from the CO?",
            "What is my raise frequency as PFR?",
        ],
    },
    "check_river_2bp_ip_pfr": {
        "description": (
            "Retrieve individual hand histories where Hero checked the river as the "
            "preflop raiser (PFR), in position (IP), in a 2-bet pot (2bp), heads-up. "
            "Returns a structured table of matching hands (position, cards, actions per street, pot, winner), not an aggregated stat."
        ),
        "examples": [
            "Show me hands where I checked the river as 2bp ip pfr",
            "Show my check river hands as preflop raiser in position",
            "Give me the top 10 hands where I checked river ip as pfr in a 2bet pot",
        ],
    },
    "fold_to_3bet_preflop": {
        "description": (
            "Retrieve individual hand histories where Hero folded to a 3Bet preflop as the original raiser (OPR). "
            "Returns a structured table of matching hands (position, cards, actions per street, pot, winner), not an aggregated stat."
        ),
        "examples": [
            "Show me hands where I folded to a 3Bet preflop",
            "Show my hands where I folded to 3Bets",
            "Give me the top 10 hands where I folded to 3Bets preflop",
        ],
    },
    "fold_vs_small_cbet_2bp_oop_pfc": {
        "description": (
            "Retrieve individual hand histories where Hero folded to a small continuation bet (20-33% pot) "
            "on the flop, as the preflop caller (PFC), out of position (OOP), in a 2-bet pot (2bp), heads-up. "
            "Returns a structured table of matching hands (position, cards, actions per street, pot, winner), not an aggregated stat."
        ),
        "examples": [
            "Show me hands where I folded to a small cbet out of position",
            "Show my hands where I folded to a small continuation bet as the caller",
            "Give me the top 10 hands where I folded vs a 20-33% pot cbet oop as pfc",
        ],
    },
}
