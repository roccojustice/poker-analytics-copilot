import pytest
from hero_responses import get_hero_response


def test_get_hero_response_returns_known_entry():
    response = get_hero_response("turn_bet_check")

    assert response["flag_column"] == "flg_t_check", "must return the real PT4 flag column, not a placeholder"
    assert response["actions"] == {True: "check", False: "bet"}, "flag value -> action name mapping must round-trip unchanged"


def test_get_hero_response_unknown_name_raises():
    with pytest.raises(ValueError):
        get_hero_response("not_a_real_response")
