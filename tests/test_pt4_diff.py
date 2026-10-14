import pytest
from pt4_diff import diff_hand_sets, normalize_hand_no


@pytest.mark.parametrize("raw, expected", [
    ("257244123456", "257244123456"),
    (" 257244123456 ", "257244123456"),
    ("257244123456.0", "257244123456"),
    (257244123456, "257244123456"),
])
def test_normalize_hand_no(raw, expected):
    assert normalize_hand_no(raw) == expected


def test_scientific_notation_is_rejected():
    with pytest.raises(ValueError, match="scientific notation"):
        normalize_hand_no("2.57244E+11")


def test_diff_is_both_directions():
    assert diff_hand_sets({"1", "2", "3"}, {"2", "3", "4"}) == {"extra": {"1"}, "missing": {"4"}}
