ATOMIC_FILTERS = {
    # Preflop filters
    "first_raise": "chps.flg_p_first_raise = true",
    "ccall": "chps.flg_p_first_raise = false",
    "faced_raise_preflop": "chps.flg_p_face_raise = true",
    "no_4bet_faced": "chps.flg_p_4bet_def_opp = false",
    "fold_preflop": "chps.flg_p_fold = true",
    "no_limpers_faced": "chps.cnt_p_face_limpers = 0",
    "total_raises": lambda op, param_name: f"hrt.total_p_raises {op} %({param_name})s",

    # Flop filters
    "heads_up_flop": "chs.cnt_players_f = 2",
    "oop_flop": "chps.flg_f_has_position = false",
    "faced_cbet_flop": "chps.flg_f_cbet_def_opp = true",
    "small_cbet_facing_pct": "chps.val_f_bet_facing_pct BETWEEN 20 AND 33",
    "no_check_raise_flop": "chps.flg_f_check_raise = false",
    "fold_flop": "chps.flg_f_fold = true",
    "no_faced_raise_flop": "chps.flg_f_face_raise = false",

    # Turn filters
    "ip_turn": "chps.flg_t_has_position = true",
    "turn_cbet_opp": "chps.flg_t_cbet_opp = true",

    # River filters
    "heads_up_river": "chs.cnt_players_r = 2",
    "ip_river": "chps.flg_r_has_position = true",
    "check_river": "chps.flg_r_check = true",
}

FILTER_RECIPES = {
    "check_river_2bp_ip_pfr": [
        "first_raise",
        ("total_raises", "=", 1),
        "no_limpers_faced",
        "heads_up_flop",
        "ip_river",
        "check_river",
    ],
    "fold_to_3bet_preflop": [
        "first_raise",
        "faced_raise_preflop",
        "no_4bet_faced",
        "fold_preflop",
        ("total_raises", ">=", 2),
        "no_limpers_faced",
    ],
    "fold_vs_small_cbet_2bp_oop_pfc": [
        "ccall",
        ("total_raises", "=", 1),
        "heads_up_flop",
        "oop_flop",
        "faced_cbet_flop",
        "small_cbet_facing_pct",
        "no_check_raise_flop",
        "fold_flop",
    ],
    "2bp_ip_pfr_turn_cbet_opp": [
        "first_raise",
        ("total_raises", "=", 1),
        "no_limpers_faced",
        "heads_up_flop",
        "ip_turn",
        "no_faced_raise_flop",
        "turn_cbet_opp",
    ]
}

def build_where_clause(recipe_name):
    if recipe_name not in FILTER_RECIPES:
        raise ValueError(f"Unknown recipe: {recipe_name}")

    where_clause = ""
    params = {}
    for i, item in enumerate(FILTER_RECIPES[recipe_name]):
        if isinstance(item, str):
            where_clause += f" AND {ATOMIC_FILTERS[item]}"
        elif isinstance(item, tuple) and len(item) == 3:
            filter_name, op, value = item
            param_name = f"{filter_name}_{i}"
            where_clause += f" AND {ATOMIC_FILTERS[filter_name](op, param_name)}"
            params[param_name] = value
        else:
            raise ValueError(f"Invalid recipe item: {item}")
    return where_clause, params
