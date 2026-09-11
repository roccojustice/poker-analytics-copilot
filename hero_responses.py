HERO_RESPONSES = {
    # bet == NOT flg_t_check is only valid combined with a recipe that already
    # guarantees the turn decision is binary (bet or check, no fold in play) —
    # see 2bp_ip_pfr_turn_cbet_opp in filter_recipes.py.
    "turn_bet_check": {
        "flag_column": "flg_t_check",
        "actions": {
            True: "check",
            False: "bet",
        },
    },
}


def get_hero_response(name):
    if name not in HERO_RESPONSES:
        raise ValueError(f"Unknown hero-response: {name}")
    return HERO_RESPONSES[name]
