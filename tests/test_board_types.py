from collections import Counter
from itertools import combinations
import pytest
from board_types import FLOP_TYPES, classify, flop_type

FIXTURES = {
    "2BWL": "AsJd2d AsJd7s AsJs9d AsKd3c AsKd8d AsKs8d AsQd5c AsQs9c AsTd3c JsTd3d JsTd6d "
            "JsTd6s JsTd7s KsJd7c KsJd7s KsJd9s KsQd3s KsQd5c KsQs9d KsTd2c KsTd2s KsTs6d QsJd4c QsJd6s "
            "QsJs8d QsTd3d QsTd5s QsTs5d",
    "BLL": "Js3d2c Js5d4s Js6d3c Js6d5c Js7d6c Js8d4d Js9d3s Js9d4s Js9d5c Ks4d2s Ks4d3c "
           "Ks5d4d Ks6d5c Ks6s2d Ks7d3c Ks8d5c Ks8d7c Ks9d3c Ks9d4c Qs4d2c Qs6d5c Qs6s2d Qs7d4s Qs7d5s "
           "Qs8d3c Qs8d7c Qs8d7s Qs9d6d Qs9d8d",
    "Low": "Ts9d5d Ts9d4c Ts8d6c Ts8d4d Ts8d2s Ts8d2c Ts7d4s Ts6d4c Ts5s3d 9s8d6d 9s8d3s "
           "9s8d2c 9s7d5d 9s6d2c 9s5d2c 9s3d2s 8s7s3d 8s5s4c 8s4d3s 7s6s2d 7s6d4c 7s6d2s 7s4d3c 7s3s2d "
           "6s5s4d 6s4s3d 5s4d2d 5s3s2d",
    "Low paired": "As4d4c Ks6s6d Ks8d8c Js2s2d Ts6s6d 9s4s4d 8s8d6c 8s7d7c 8s5s5d 5s5d5c 5s3d3c 4s2s2d",
    "High paired": "AsAd6d AsQsQd AsAd3d KsKdKc KsKdTc QsQd2c QsJdJc JsJd4c TsTd9d TsTd7c 9s9d5c 9s9d7d",
    "A high": "As9s4d As9d7c As9d7s As8s5d As8d6s As7d5c As5d2c As4s2d As7d2c As3d2s As6d3c",
    "Monotone": "As5s3s KsJs5s Qs3s2s JsTs9s Ts7s4s 8s6s2s",
    "3BW": "AsKdTc AsQsJd AsQdTs KsQdJc QhJhTd",
}
CASES = [(type_, flop) for type_, flops in FIXTURES.items() for flop in flops.split()]


def parse(flop):
    return [(flop[i], flop[i + 1]) for i in range(0, 6, 2)]


@pytest.mark.parametrize("type_, flop", CASES)
def test_user_examples(type_, flop):
    assert classify(parse(flop)) == type_


@pytest.mark.parametrize("flop, type_", [
    ("TsTd2c", "High paired"), ("8s8d2c", "Low paired"), ("Ts9d8c", "Low"), ("AsTd3c", "2BWL"),
    ("KsKdKc", "High paired"), ("5s5d5c", "Low paired"), ("AsKsQs", "Monotone"),
])
def test_boundaries(flop, type_):
    assert classify(parse(flop)) == type_


def test_counts_over_every_flop():
    deck = [(r, s) for r in "23456789TJQKA" for s in "cdhs"]
    counts = Counter(classify(list(flop)) for flop in combinations(deck, 3))
    assert counts == {
        "Low paired": 2044, "High paired": 1752, "3BW": 600, "2BWL": 4800,
        "A high": 1680, "BLL": 5040, "Low": 5040, "Monotone": 1144,
    }


def test_registry_order():
    assert FLOP_TYPES == ("BLL", "Low", "2BWL", "Low paired", "High paired", "A high", "Monotone", "3BW")


def test_flop_type_decodes_pt4_ids():
    assert flop_type(52, 51, 50) == "Monotone"  # As Ks Qs
    assert flop_type(13, 26, 39) == "High paired"  # Ac Ad Ah
    with pytest.raises(ValueError):
        flop_type(0, 1, 2)
