ATOMIC_FILTERS = {
    # Preflop filters
    "first_raise": "chps.flg_p_first_raise = true",
    "ccall": "chps.flg_p_first_raise = false",
    "faced_raise_preflop": "chps.flg_p_face_raise = true",
    "no_face_raise_preflop": "chps.flg_p_face_raise = false",
    "no_4bet_faced": "chps.flg_p_4bet_def_opp = false",
    "fold_preflop": "chps.flg_p_fold = true",
    "no_fold_preflop": "chps.flg_p_fold = false",
    "no_limpers_faced": "chps.cnt_p_face_limpers = 0",
    "total_raises": lambda op, param_name: f"hrt.total_p_raises {op} %({param_name})s",
    "own_raises": lambda op, param_name: f"chps.cnt_p_raise {op} %({param_name})s",
    "faced_3bet_preflop": "chps.flg_p_3bet_def_opp = true",
    "no_4bet_made": "chps.flg_p_4bet = false",
    "no_squeeze_def_faced": "chps.flg_p_squeeze_def_opp = false",
    "made_3bet": "chps.flg_p_3bet = true",
    "had_3bet_opp": "chps.flg_p_3bet_opp = true",
    "no_squeeze_made": "chps.flg_p_squeeze = false",
    "vpip": "chps.flg_vpip = true",
    "no_first_raise": "chps.flg_p_first_raise = false",
    "no_3bet_made": "chps.flg_p_3bet = false",
    "no_3bet_def_faced": "chps.flg_p_3bet_def_opp = false",

    # Flop filters
    "heads_up_flop": "chs.cnt_players_f = 2",
    "ip_flop": "chps.flg_f_has_position = true",
    "oop_flop": "chps.flg_f_has_position = false",
    "faced_cbet_flop": "chps.flg_f_cbet_def_opp = true",
    "small_cbet_facing_pct": "chps.val_f_bet_facing_pct BETWEEN 20 AND 33",
    "no_check_raise_flop": "chps.flg_f_check_raise = false",
    "fold_flop": "chps.flg_f_fold = true",
    "no_faced_raise_flop": "chps.flg_f_face_raise = false",

    # Turn filters
    "ip_turn": "chps.flg_t_has_position = true",
    "oop_turn": "chps.flg_t_has_position = false",
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
    # Simplified 2bp_*_pfr formula, no total_raises=1 (see SCHEMA_NOTES.md).
    "2bp_ip_pfr_turn_cbet_opp": [
        "first_raise",
        "no_limpers_faced",
        "no_face_raise_preflop",
        "heads_up_flop",
        "ip_turn",
        "no_faced_raise_flop",
        "turn_cbet_opp",
    ],
    "2bp_oop_pfr_turn_cbet_opp": [
        "first_raise",
        "no_limpers_faced",
        "no_face_raise_preflop",
        "heads_up_flop",
        "oop_turn",
        "no_faced_raise_flop",
        "turn_cbet_opp",
    ],
    # Validated 3bp_oop_pfr formula (SCHEMA_NOTES.md, Session 47, 1687 hands).
    "3bp_oop_pfr_turn_cbet_opp": [
        "made_3bet",
        "had_3bet_opp",
        ("own_raises", "=", 1),
        "faced_raise_preflop",
        "no_4bet_faced",
        "no_squeeze_made",
        "heads_up_flop",
        "oop_turn",
        "no_faced_raise_flop",
        "turn_cbet_opp",
    ],
    # Validated 3bp_ip_pfr formula (SCHEMA_NOTES.md, Session 47, 2067 hands).
    "3bp_ip_pfr_turn_cbet_opp": [
        "made_3bet",
        "had_3bet_opp",
        ("own_raises", "=", 1),
        "faced_raise_preflop",
        "no_4bet_faced",
        "no_squeeze_made",
        "heads_up_flop",
        "ip_turn",
        "no_faced_raise_flop",
        "turn_cbet_opp",
    ],
    # Validated 3bp_ip_pfc formula (SCHEMA_NOTES.md, Session 47, 1557 hands,
    # exact hand_no match) + faced_cbet_flop as the situation layer.
    # no_limpers_faced added Session 53 after a live PT4 cross-check: unlike
    # the 3bp_*_pfc case Session 47 dismissed this atomic for (there, Hero was
    # the 3-bettor and cnt_p_face_limpers reflects the *opener's* row, not
    # Hero's), here Hero IS the opener (first_raise), so cnt_p_face_limpers is
    # genuinely Hero's own "did I open over a limper" state.
    # Validated 2bp_ip_pfc formula (SCHEMA_NOTES.md, Session 46, 2569 hands).
    "2bp_ip_pfc_faced_cbet_flop": [
        "heads_up_flop",
        "ip_flop",
        "vpip",
        "no_first_raise",
        "no_3bet_made",
        ("own_raises", "=", 0),
        "faced_raise_preflop",
        "no_fold_preflop",
        "no_3bet_def_faced",
        "faced_cbet_flop",
    ],
    "3bp_ip_pfc_faced_cbet_flop": [
        "heads_up_flop",
        "ip_flop",
        ("own_raises", "<=", 1),
        "faced_3bet_preflop",
        "no_4bet_made",
        "no_4bet_faced",
        "no_fold_preflop",
        "no_squeeze_def_faced",
        "first_raise",
        "no_limpers_faced",
        "faced_cbet_flop",
    ],
    "2bp_oop_pfc_faced_cbet_flop": [
        "heads_up_flop",
        "oop_flop",
        "vpip",
        "no_first_raise",
        "no_3bet_made",
        ("own_raises", "=", 0),
        "faced_raise_preflop",
        "no_fold_preflop",
        "no_3bet_def_faced",
        "faced_cbet_flop",
    ],
    # no_4bet_faced is redundant OOP (SCHEMA_NOTES.md), kept to mirror the IP recipe.
    "3bp_oop_pfc_faced_cbet_flop": [
        "heads_up_flop",
        "oop_flop",
        ("own_raises", "<=", 1),
        "faced_3bet_preflop",
        "no_4bet_made",
        "no_4bet_faced",
        "no_fold_preflop",
        "no_squeeze_def_faced",
        "first_raise",
        "no_limpers_faced",
        "faced_cbet_flop",
    ],
}

def build_where_clause(recipe_name):
    if recipe_name not in FILTER_RECIPES:
        raise ValueError(f"Unknown recipe: {recipe_name}")
    return assemble_where(FILTER_RECIPES[recipe_name])

def assemble_where(items):
    where_clause = ""
    params = {}
    for i, item in enumerate(items):
        if isinstance(item, str):
            where_clause += f" AND {ATOMIC_FILTERS[item]}"
        elif isinstance(item, tuple) and len(item) == 3:
            filter_name, op, value = item
            param_name = f"{filter_name}_{i}"
            where_clause += f" AND {ATOMIC_FILTERS[filter_name](op, param_name)}"
            params[param_name] = value
        else:
            raise ValueError(f"Invalid item: {item}")
    return where_clause, params