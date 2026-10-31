import pandas as pd
from pt4_diff import filter_by_label, filter_by_result
import pytest
from pt4_diff import diff_hand_sets, normalize_hand_no


@pytest.mark.parametrize("raw, expected", [
    ("257244123456", "257244123456"),
    (" 257244123456 ", "257244123456"),
    ("257244123456.0", "257244123456"),
    (257244123456, "257244123456"),
    ("HE257244123456", "HE257244123456"),
])
def test_normalize_hand_no(raw, expected):
    assert normalize_hand_no(raw) == expected


def test_scientific_notation_is_rejected():
    with pytest.raises(ValueError, match="scientific notation"):
        normalize_hand_no("2.57244E+11")


def test_diff_is_both_directions():
    assert diff_hand_sets({"1", "2", "3"}, {"2", "3", "4"}) == {"extra": {"1"}, "missing": {"4"}}


@pytest.mark.parametrize("low, high, expected", [
    (None, -5.0, [1, 2]),
    (5.0, None, [4, 5]),
    (-5.0, 5.0, [2, 3, 4]),
    (None, None, [1, 2, 3, 4, 5]),
])
def test_filter_by_result_bounds_are_inclusive(low, high, expected):
    hands = pd.DataFrame({"id_hand": [1, 2, 3, 4, 5], "result_bb": [-8.0, -5.0, 0.0, 5.0, 9.5]})
    assert list(filter_by_result(hands, low, high)["id_hand"]) == expected


def test_filter_by_result_on_no_hands_is_empty():
    assert filter_by_result(pd.DataFrame(), -5.0, None).empty


def test_filter_by_label_keeps_only_that_label():
    hands = pd.DataFrame({"id_hand": [1, 2, 3], "measured_action": ["Bs", "Bm", "Bs"]})
    assert list(filter_by_label(hands, "Bs")["id_hand"]) == [1, 3]


def test_no_label_keeps_every_hand():
    hands = pd.DataFrame({"id_hand": [1, 2], "measured_action": ["Bs", "X"]})
    assert list(filter_by_label(hands, None)["id_hand"]) == [1, 2]


def test_overall_label_keeps_its_sized_children():
    hands = pd.DataFrame({"id_hand": [1, 2, 3], "measured_action": ["Bs", "Bo", "X"]})
    assert list(filter_by_label(hands, "B")["id_hand"]) == [1, 2]
