HERO_RESPONSES = {
    # bet == NOT flg_t_check is only valid combined with a recipe that already
    # guarantees the turn decision is binary (bet or check, no fold in play) —
    # see 2bp_ip_pfr_turn_cbet_opp in filter_recipes.py.
    "turn_bet_check": {
        "conditions": [
            ("check", "chps.flg_t_check = true"),
            ("bet", "chps.flg_t_check = false"),
        ],
    },
    # Facing a bet, raise/call/fold. Priority matters: raise is checked first
    # so a raise that later folds/calls a re-raise still counts as raise —
    # that's Hero's actual decision at this bet-facing point. Validated
    # against Postgres (Session 53): on 3bp_ip_pfc_faced_cbet_flop, 1087 total,
    # 102 raise / 388 fold / 597 call, exhaustive and mutually exclusive by
    # construction (each condition excludes the ones above it).
    "flop_raise_call_fold": {
        "conditions": [
            ("raise", "chps.cnt_f_raise >= 1"),
            ("fold", "chps.cnt_f_raise = 0 AND chps.flg_f_fold = true"),
            ("call", "chps.cnt_f_raise = 0 AND chps.flg_f_fold = false"),
        ],
    },
}


def get_hero_response(name):
    if name not in HERO_RESPONSES:
        raise ValueError(f"Unknown hero-response: {name}")
    return HERO_RESPONSES[name]
