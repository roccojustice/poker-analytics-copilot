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
    "2bp_ip_pfr_turn_cbet_opp": {
        "description": (
            "2bp ip pfr - B-B opportunity (TURN decision). Single-raised pot (2bp, also called srp), "
            "heads-up; Hero opened preflop (PFR), is in position (IP), cbet the flop (first barrel), "
            "got called, and now has the chance to bet the turn again. "
            "Measures Hero's TURN bet/check. Also called: turn cbet opportunity, "
            "2nd barrel / double barrel opportunity."
        ),
        "examples": [
            "srp ip pfr - B-B frequencies",
            "how often do I double barrel the turn as 2bp ip pfr?",
            "show me hands as 2bp ip pfr where I cbet flop, got called, and had the chance to bet the turn",
        ],
    },
    "2bp_oop_pfr_turn_cbet_opp": {
        "description": (
            "2bp oop pfr - B-B opportunity (TURN decision). Single-raised pot (2bp, also called srp), "
            "heads-up; Hero opened preflop (PFR), is out of position (OOP), cbet the flop (first barrel), "
            "got called, and now has the chance to bet the turn again. "
            "Measures Hero's TURN bet/check. Also called: turn cbet opportunity, "
            "2nd barrel / double barrel opportunity."
        ),
        "examples": [
            "srp oop pfr - B-B frequencies",
            "how often do I double barrel the turn as 2bp oop pfr?",
            "show me hands as 2bp oop pfr where I cbet flop, got called, and had the chance to bet the turn",
        ],
    },
    "3bp_oop_pfr_turn_cbet_opp": {
        "description": (
            "3bp oop pfr - B-B opportunity (TURN decision). 3-bet pot (3bp), heads-up; "
            "Hero made the 3bet preflop (PFR), is out of position (OOP), cbet the flop (first barrel), "
            "got called, and now has the chance to bet the turn again. "
            "Measures Hero's TURN bet/check. Also called: turn cbet opportunity, "
            "2nd barrel / double barrel opportunity."
        ),
        "examples": [
            "3bp oop pfr - B-B frequencies",
            "how often do I double barrel the turn as 3bp oop pfr?",
            "show me hands as 3bp oop pfr where I cbet flop, got called, and had the chance to bet the turn",
        ],
    },
    "3bp_ip_pfr_turn_cbet_opp": {
        "description": (
            "3bp ip pfr - B-B opportunity (TURN decision). 3-bet pot (3bp), heads-up; "
            "Hero made the 3bet preflop (PFR), is in position (IP), cbet the flop (first barrel), "
            "got called, and now has the chance to bet the turn again. "
            "Measures Hero's TURN bet/check. Also called: turn cbet opportunity, "
            "2nd barrel / double barrel opportunity."
        ),
        "examples": [
            "3bp ip pfr - B-B frequencies",
            "how often do I double barrel the turn as 3bp ip pfr?",
            "show me hands as 3bp ip pfr where I cbet flop, got called, and had the chance to bet the turn",
        ],
    },
    "2bp_ip_pfc_faced_cbet_flop": {
        "description": (
            "2bp ip pfc vs cbet (FLOP decision). Single-raised pot (2bp, also called srp), heads-up; "
            "Hero called the open preflop (PFC), is in position (IP), and faces the opener's cbet "
            "on the FLOP. Measures Hero's FLOP raise/call/fold. Also called: vs b, vs flop cbet."
        ),
        "examples": [
            "srp ip pfc vs cbet frequencies",
            "what are my raise, call and fold frequencies as 2bp ip pfc facing a flop cbet?",
            "show me hands as 2bp ip pfc where the preflop raiser cbet the flop and I had to respond",
        ],
    },
    "3bp_ip_pfc_faced_cbet_flop": {
        "description": (
            "3bp ip pfc vs cbet (FLOP decision). 3-bet pot (3bp), heads-up; "
            "Hero called the 3bet preflop (PFC), is in position (IP), and faces the 3bettor's cbet "
            "on the FLOP. Measures Hero's FLOP raise/call/fold. Also called: vs b, vs flop cbet."
        ),
        "examples": [
            "3bp ip pfc vs b frequencies",
            "what are my raise, call and fold frequencies as 3bp ip pfc facing a flop cbet?",
            "show me hands as 3bp ip pfc where the 3bettor cbet the flop and I had to respond",
        ],
    },
    "2bp_oop_pfc_faced_cbet_flop": {
        "description": (
            "2bp oop pfc vs cbet (FLOP decision). Single-raised pot (2bp, also called srp), heads-up; "
            "Hero called the open preflop (PFC), is out of position (OOP), checked, and faces the "
            "opener's cbet on the FLOP. Measures Hero's FLOP raise/call/fold. Also called: vs b, vs flop cbet."
        ),
        "examples": [
            "srp oop pfc vs cbet frequencies",
            "what are my check-raise, call and fold frequencies as 2bp oop pfc facing a flop cbet?",
            "show me hands as 2bp oop pfc where I checked, the preflop raiser cbet the flop, and I had to respond",
        ],
    },
    "3bp_oop_pfc_faced_cbet_flop": {
        "description": (
            "3bp oop pfc vs cbet (FLOP decision). 3-bet pot (3bp), heads-up; "
            "Hero called the 3bet preflop (PFC), is out of position (OOP), checked, and faces the "
            "3bettor's cbet on the FLOP. Measures Hero's FLOP raise/call/fold. Also called: vs b, vs flop cbet."
        ),
        "examples": [
            "3bp oop pfc vs cbet frequencies",
            "what are my check-raise, call and fold frequencies as 3bp oop pfc facing a flop cbet?",
            "show me hands as 3bp oop pfc where I checked, the 3bettor cbet the flop, and I had to respond",
        ],
    },
    "3bp_ip_pfc_faced_barrel_turn": {
        "description": (
            "3bp ip pfc vs B-B (TURN decision). 3-bet pot (3bp); "
            "Hero called the 3bet preflop (PFC), is in position (IP), called the flop cbet, "
            "and faces a second bet on the TURN. Measures Hero's TURN raise/call/fold. "
            "Also called: vs 2nd barrel, vs double barrel, vs turn cbet / cbet en el turn."
        ),
        "examples": [
            "frecuencias 3bp ip pfc vs double barrel",
            "3bp ip pfc vs turn barrel",
            "3bp ip pfc: me apuestan flop y turn, qué hago en el turn?",
        ],
    },
}
