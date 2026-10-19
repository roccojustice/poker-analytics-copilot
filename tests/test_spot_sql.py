from datetime import date
from decimal import Decimal
import pytest
from line_parser import parse_line, SpotInputError
from spot_sql import build_spot_query, splits_by_size, FORMATIONS, PREFLOP_CONTEXTS


def build(pot, position, role, line, formations=()):
    spec = parse_line(line, role, position)
    return build_spot_query(pot, position, role, spec, formations)


def test_completed_streets_bind_exact_strings():
    where, params, _ = build("2bp", "ip", "pfr", "- B-?")
    assert "h_f.action = %(h_f)s" in where
    assert "v_f.action = %(v_f)s" in where
    assert params["h_f"] == "B"
    assert params["v_f"] == "XC"


def test_decision_street_binds_prefixes_and_measured_set():
    where, params, measured_sql = build("2bp", "oop", "pfc", "vs B?")
    assert "h_f.action LIKE %(h_f_prefix)s" in where
    assert "v_f.action LIKE %(v_f_prefix)s" in where
    assert params["h_f_prefix"] == "X%"
    assert params["v_f_prefix"] == "B%"
    letter = "substr(h_f.action, %(measure_pos)s, 1)"
    assert measured_sql.startswith(letter)
    assert params["measure_pos"] == 2
    assert f"{letter} = ANY(%(measured)s)" in where
    assert params["measured"] == ["F", "C", "R"]


def test_line_letters_never_reach_the_sql_text():
    where, _, _ = build("3bp", "ip", "pfc", "vs B-XC-X?")
    assert "'XC'" not in where and "'B'" not in where


def test_preflop_context_and_position_are_applied():
    where, params, _ = build("3bp", "oop", "pfr", "- B-?")
    assert "chps.flg_p_3bet = true" in where
    assert "chps.flg_f_has_position = false" in where
    assert "chs.cnt_players_f = 2" in where
    assert params["own_raises_2"] == 1  # assemble_where names it <atom>_<index>


def test_every_pot_role_pair_has_a_context():
    assert set(PREFLOP_CONTEXTS) == {("2bp", "pfr"), ("2bp", "pfc"), ("3bp", "pfr"), ("3bp", "pfc")}


@pytest.mark.parametrize("formations", [(), []])
def test_no_formation_adds_no_seat_condition(formations):
    where, params, _ = build("2bp", "ip", "pfr", "- B-?", formations)
    assert "chps.position" not in where
    assert "hero_pos_0" not in params


@pytest.mark.parametrize("position, hero_pos, villain_pos", [("oop", 8, 0), ("ip", 0, 8)])
def test_formation_maps_hero_seat_from_position(position, hero_pos, villain_pos):
    role, line = ("pfc", "vs B?") if position == "oop" else ("pfr", "- B-?")
    where, params, _ = build("2bp", position, role, line, ["BB vs BTN"])
    assert "(chps.position, v.position) IN ((%(hero_pos_0)s, %(villain_pos_0)s))" in where
    assert (params["hero_pos_0"], params["villain_pos_0"]) == (hero_pos, villain_pos)


def test_several_formations_are_ored():
    where, params, _ = build("2bp", "oop", "pfc", "vs B?", ["BB vs BTN", "BB vs CO"])
    assert (
        "(chps.position, v.position) IN ((%(hero_pos_0)s, %(villain_pos_0)s), "
        "(%(hero_pos_1)s, %(villain_pos_1)s))"
    ) in where
    assert (params["hero_pos_0"], params["villain_pos_0"]) == (8, 0)
    assert (params["hero_pos_1"], params["villain_pos_1"]) == (8, 1)


def test_duplicate_formations_bind_once():
    where, params, _ = build("2bp", "oop", "pfc", "vs B?", ["BB vs BTN", "BB vs BTN"])
    assert "hero_pos_1" not in params
    assert "%(hero_pos_1)s" not in where


def test_formations_are_oop_first_and_complete():
    assert len(FORMATIONS) == 15
    assert "BB vs BTN" in FORMATIONS and "SB vs BB" in FORMATIONS
    assert "BTN vs BB" not in FORMATIONS


@pytest.mark.parametrize("pot, formations, message", [
    ("4bp", [], "Unknown pot: 4bp"),
    ("2bp", ["BTN vs BB"], "Unknown formation: BTN vs BB"),
    ("2bp", ["BB vs BTN", "XX"], "Unknown formation: XX"),
])
def test_bad_bar_values_raise(pot, formations, message):
    spec = parse_line("- B-?", "pfr", "ip")
    with pytest.raises(SpotInputError, match=message):
        build_spot_query(pot, "ip", "pfr", spec, formations)


def test_no_dates_add_no_date_condition():
    where, params, _ = build("2bp", "ip", "pfr", "- B-?")
    assert "date_played" not in where
    assert not {"date_from", "date_to"} & set(params)


def test_date_range_is_bound_and_inclusive_of_the_end_day():
    spec = parse_line("- B-?", "pfr", "ip")
    where, params, _ = build_spot_query("2bp", "ip", "pfr", spec, (), date(2026, 9, 1), date(2026, 10, 15))
    assert "chps.date_played >= %(date_from)s" in where
    assert "chps.date_played < %(date_to)s" in where
    assert params["date_from"] == date(2026, 9, 1)
    assert params["date_to"] == date(2026, 10, 16)  # exclusive bound = the day after


def test_open_ended_date_range_binds_one_side():
    spec = parse_line("- B-?", "pfr", "ip")
    where, params, _ = build_spot_query("2bp", "ip", "pfr", spec, (), date_from=date(2026, 9, 1))
    assert "%(date_from)s" in where and "%(date_to)s" not in where
    assert "date_to" not in params


def test_date_from_after_date_to_raises():
    spec = parse_line("- B-?", "pfr", "ip")
    with pytest.raises(SpotInputError, match="From date is after To date"):
        build_spot_query("2bp", "ip", "pfr", spec, (), date(2026, 10, 2), date(2026, 10, 1))


def test_sized_street_binds_decimal_bounds_against_its_pot():
    where, params, _ = build("2bp", "oop", "pfc", "vs Bm?")
    bet = "(chps.amt_f_bet_made + chps.amt_f_bet_facing)"
    assert f"{bet} >= %(size_f_lo)s * chs.amt_pot_f" in where
    assert f"{bet} < %(size_f_hi)s * chs.amt_pot_f" in where
    assert params["size_f_lo"] == Decimal("0.45") and type(params["size_f_lo"]) is Decimal
    assert params["size_f_hi"] == Decimal("0.70") and type(params["size_f_hi"]) is Decimal


def test_overbet_has_no_upper_bound():
    where, params, _ = build("2bp", "oop", "pfc", "vs Bo?")
    assert "%(size_f_lo)s" in where and "size_f_hi" not in where
    assert params["size_f_lo"] == Decimal("1.05") and "size_f_hi" not in params


def test_each_sized_street_gets_its_own_bounds():
    where, params, _ = build("2bp", "ip", "pfc", "vs Bs-XCl-X?")
    assert params["size_f_hi"] == Decimal("0.45")
    assert (params["size_t_lo"], params["size_t_hi"]) == (Decimal("0.70"), Decimal("1.05"))
    assert "chs.amt_pot_t" in where and "size_r_lo" not in params


def test_no_suffix_adds_no_size_condition():
    where, params, _ = build("3bp", "ip", "pfc", "vs B-XC-X?")
    assert "bet_made" not in where
    assert not [k for k in params if k.startswith("size_")]  # bucket_* belong to the B/X label


def test_bet_decision_labels_bets_by_size():
    where, params, measured_sql = build("2bp", "ip", "pfr", "- B-?")
    letter = "substr(h_t.action, %(measure_pos)s, 1)"
    assert f"{letter} = ANY(%(measured)s)" in where  # filter on the letter, not the label
    assert measured_sql.startswith(f"CASE WHEN {letter} = 'B' THEN 'B' || CASE ")
    for key in ("S", "M", "L"):
        assert f"< %(bucket_{key})s * chs.amt_pot_t THEN '{key.lower()}'" in measured_sql
    assert "ELSE 'o' END" in measured_sql and measured_sql.endswith(f"ELSE {letter} END")
    assert (params["bucket_S"], params["bucket_M"], params["bucket_L"]) == (
        Decimal("0.45"), Decimal("0.70"), Decimal("1.05"))


LETTER_F = "substr(h_f.action, %(measure_pos)s, 1)"


def test_facing_decision_without_suffix_labels_the_response_by_size():
    where, params, measured_sql = build("2bp", "oop", "pfc", "vs B?")
    assert f"{LETTER_F} = ANY(%(measured)s)" in where  # filter on the letter, not the label
    assert measured_sql.startswith(f"{LETTER_F} || CASE ")
    for key in ("S", "M", "L"):
        assert f"< %(bucket_{key})s * chs.amt_pot_f THEN '{key.lower()}'" in measured_sql
    assert measured_sql.endswith("ELSE 'o' END")
    assert (params["bucket_S"], params["bucket_M"], params["bucket_L"]) == (
        Decimal("0.45"), Decimal("0.70"), Decimal("1.05"))


def test_facing_decision_with_suffix_label_stays_the_letter():
    _, params, measured_sql = build("2bp", "oop", "pfc", "vs Bs?")
    assert measured_sql == LETTER_F
    assert "bucket_S" not in params


def test_turn_split_after_a_sized_flop_keeps_both_bounds():
    _, params, measured_sql = build("2bp", "oop", "pfc", "vs Bs-B?")
    assert "size_f_lo" in params and "bucket_S" in params
    assert "* chs.amt_pot_t THEN 's'" in measured_sql


@pytest.mark.parametrize("line, role, position, expected", [
    ("vs B?", "pfc", "oop", True),
    ("- B?", "pfr", "ip", True),
    ("vs Bs?", "pfc", "oop", False),
    ("- B-?", "pfr", "ip", False),
])
def test_splits_by_size(line, role, position, expected):
    assert splits_by_size(parse_line(line, role, position)) is expected
