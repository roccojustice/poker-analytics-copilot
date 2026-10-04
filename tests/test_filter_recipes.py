import pytest
from filter_recipes import assemble_where, build_where_clause


def test_assemble_where_mixed_list():
    items = ["first_raise", ("total_raises", ">=", 2), "heads_up_flop"]
    where_sql, params = assemble_where(items)

    assert where_sql == (
        " AND chps.flg_p_first_raise = true"
        " AND hrt.total_p_raises >= %(total_raises_1)s"
        " AND chs.cnt_players_f = 2"
    ), "string items must resolve to their SQL fragment, tuple items to a bound placeholder"
    assert params == {"total_raises_1": 2}, "param name carries the enumerate index, value is bound not interpolated"


def test_assemble_where_repeated_atomic_gets_distinct_param_names():
    items = [("total_raises", "=", 1), ("total_raises", ">=", 2)]
    where_sql, params = assemble_where(items)

    assert where_sql == (
        " AND hrt.total_p_raises = %(total_raises_0)s"
        " AND hrt.total_p_raises >= %(total_raises_1)s"
    ), "the same atomic used twice must produce position-distinct placeholders"
    assert params == {"total_raises_0": 1, "total_raises_1": 2}, "no param-name collision across positions"


def test_assemble_where_rejects_malformed_item():
    with pytest.raises(ValueError):
        assemble_where([("total_raises", "=")])


def test_build_where_clause_unknown_recipe():
    with pytest.raises(ValueError):
        build_where_clause("not_a_real_recipe")


def test_build_where_clause_3bp_oop_pfr_turn_cbet_opp():
    where_sql, params = build_where_clause("3bp_oop_pfr_turn_cbet_opp")

    assert where_sql == (
        " AND chps.flg_p_3bet = true"
        " AND chps.flg_p_3bet_opp = true"
        " AND chps.cnt_p_raise = %(own_raises_2)s"
        " AND chps.flg_p_face_raise = true"
        " AND chps.flg_p_4bet_def_opp = false"
        " AND chps.flg_p_squeeze = false"
        " AND chs.cnt_players_f = 2"
        " AND chps.flg_t_has_position = false"
        " AND chps.flg_f_face_raise = false"
        " AND chps.flg_t_cbet_opp = true"
    ), "validated Session 47 3bp_oop_pfr formula (SCHEMA_NOTES.md, 1687 hands) + bet-flop/turn-cbet-opp situation atoms"
    assert params == {"own_raises_2": 1}


def test_build_where_clause_2bp_ip_pfr_turn_cbet_opp():
    where_sql, params = build_where_clause("2bp_ip_pfr_turn_cbet_opp")

    assert where_sql == (
        " AND chps.flg_p_first_raise = true"
        " AND chps.cnt_p_face_limpers = 0"
        " AND chps.flg_p_face_raise = false"
        " AND chs.cnt_players_f = 2"
        " AND chps.flg_t_has_position = true"
        " AND chps.flg_f_face_raise = false"
        " AND chps.flg_t_cbet_opp = true"
    ), "refactored to the Session 46 simplified 2bp_*_pfr formula, verified 0/0 hand_no diff against the old total_raises=1 form (4113 hands)"
    assert params == {}


def test_build_where_clause_3bp_ip_pfr_turn_cbet_opp():
    where_sql, params = build_where_clause("3bp_ip_pfr_turn_cbet_opp")

    assert where_sql == (
        " AND chps.flg_p_3bet = true"
        " AND chps.flg_p_3bet_opp = true"
        " AND chps.cnt_p_raise = %(own_raises_2)s"
        " AND chps.flg_p_face_raise = true"
        " AND chps.flg_p_4bet_def_opp = false"
        " AND chps.flg_p_squeeze = false"
        " AND chs.cnt_players_f = 2"
        " AND chps.flg_t_has_position = true"
        " AND chps.flg_f_face_raise = false"
        " AND chps.flg_t_cbet_opp = true"
    ), "validated Session 47 3bp_ip_pfr formula (SCHEMA_NOTES.md, 2067 hands) + bet-flop/turn-cbet-opp situation atoms"
    assert params == {"own_raises_2": 1}


def test_build_where_clause_2bp_ip_pfc_faced_cbet_flop():
    where_sql, params = build_where_clause("2bp_ip_pfc_faced_cbet_flop")

    assert where_sql == (
        " AND chs.cnt_players_f = 2"
        " AND chps.flg_f_has_position = true"
        " AND chps.flg_vpip = true"
        " AND chps.flg_p_first_raise = false"
        " AND chps.flg_p_3bet = false"
        " AND chps.cnt_p_raise = %(own_raises_5)s"
        " AND chps.flg_p_face_raise = true"
        " AND chps.flg_p_fold = false"
        " AND chps.flg_p_3bet_def_opp = false"
        " AND chps.flg_f_cbet_def_opp = true"
    ), "validated Session 46 2bp_ip_pfc formula (SCHEMA_NOTES.md, 2569 hands) + faced_cbet_flop situation atom"
    assert params == {"own_raises_5": 0}


def test_build_where_clause_2bp_oop_pfr_turn_cbet_opp():
    where_sql, params = build_where_clause("2bp_oop_pfr_turn_cbet_opp")

    assert where_sql == (
        " AND chps.flg_p_first_raise = true"
        " AND chps.cnt_p_face_limpers = 0"
        " AND chps.flg_p_face_raise = false"
        " AND chs.cnt_players_f = 2"
        " AND chps.flg_t_has_position = false"
        " AND chps.flg_f_face_raise = false"
        " AND chps.flg_t_cbet_opp = true"
    ), "preflop-context via the Session 46 simplified 2bp_*_pfr formula (first_raise + no_limpers_faced + no_face_raise_preflop), oop via flg_t_has_position"
    assert params == {}


def test_build_where_clause_2bp_oop_pfc_faced_cbet_flop():
    where_sql, params = build_where_clause("2bp_oop_pfc_faced_cbet_flop")

    assert where_sql == (
        " AND chs.cnt_players_f = 2"
        " AND chps.flg_f_has_position = false"
        " AND chps.flg_vpip = true"
        " AND chps.flg_p_first_raise = false"
        " AND chps.flg_p_3bet = false"
        " AND chps.cnt_p_raise = %(own_raises_5)s"
        " AND chps.flg_p_face_raise = true"
        " AND chps.flg_p_fold = false"
        " AND chps.flg_p_3bet_def_opp = false"
        " AND chps.flg_f_cbet_def_opp = true"
    ), "validated Session 46 2bp_oop_pfc formula (SCHEMA_NOTES.md, 6731 hands) + faced_cbet_flop situation atom"
    assert params == {"own_raises_5": 0}


def test_build_where_clause_3bp_oop_pfc_faced_cbet_flop():
    where_sql, params = build_where_clause("3bp_oop_pfc_faced_cbet_flop")

    assert where_sql == (
        " AND chs.cnt_players_f = 2"
        " AND chps.flg_f_has_position = false"
        " AND chps.cnt_p_raise <= %(own_raises_2)s"
        " AND chps.flg_p_3bet_def_opp = true"
        " AND chps.flg_p_4bet = false"
        " AND chps.flg_p_4bet_def_opp = false"
        " AND chps.flg_p_fold = false"
        " AND chps.flg_p_squeeze_def_opp = false"
        " AND chps.flg_p_first_raise = true"
        " AND chps.cnt_p_face_limpers = 0"
        " AND chps.flg_f_cbet_def_opp = true"
    ), "validated Session 47 3bp_oop_pfc formula (SCHEMA_NOTES.md, 1374 hands) + faced_cbet_flop situation atom"
    assert params == {"own_raises_2": 1}


def test_build_where_clause_3bp_ip_pfc_faced_barrel_turn():
    where_sql, params = build_where_clause("3bp_ip_pfc_faced_barrel_turn")

    assert where_sql == (
        " AND chs.cnt_players_f = 2"
        " AND chps.flg_f_has_position = true"
        " AND chps.cnt_p_raise <= %(own_raises_2)s"
        " AND chps.flg_p_3bet_def_opp = true"
        " AND chps.flg_p_4bet = false"
        " AND chps.flg_p_4bet_def_opp = false"
        " AND chps.flg_p_fold = false"
        " AND chps.flg_p_squeeze_def_opp = false"
        " AND chps.flg_p_first_raise = true"
        " AND chps.cnt_p_face_limpers = 0"
        " AND chps.flg_f_cbet_def_opp = true"
        " AND chps.flg_t_cbet_def_opp = true"
    ), "3bp_ip_pfc_faced_cbet_flop + faced_cbet_turn situation atom"
    assert params == {"own_raises_2": 1}
