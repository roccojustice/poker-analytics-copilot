import pytest
from hero_responses import get_hero_response


def test_get_hero_response_returns_known_entry():
    response = get_hero_response("turn_bet_check")

    assert response["conditions"] == [
        ("check", "chps.flg_t_check = true"),
        ("bet", "chps.flg_t_check = false"),
    ], "conditions must be an ordered (action_name, sql_condition) list, first match wins"


def test_get_hero_response_unknown_name_raises():
    with pytest.raises(ValueError):
        get_hero_response("not_a_real_response")


def test_flop_raise_call_fold_conditions_are_priority_ordered():
    response = get_hero_response("flop_raise_call_fold")

    assert response["conditions"] == [
        ("raise", "chps.cnt_f_raise >= 1"),
        ("fold", "chps.cnt_f_raise = 0 AND chps.flg_f_fold = true"),
        ("call", "chps.cnt_f_raise = 0 AND chps.flg_f_fold = false"),
    ], (
        "raise must be checked first so a raise-then-fold-to-a-reraise hand still counts as raise, "
        "matching Hero's actual decision at the original bet-facing point"
    )
