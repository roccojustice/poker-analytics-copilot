from collections import Counter
from itertools import combinations
import pytest
import random

from board_types import (
    FLOP_TYPES, RIVER_LABELS, TURN_LABELS, classify, flop_type, river_labels, runout_labels, turn_labels,
)

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
    return [(flop[i], flop[i + 1]) for i in range(0, len(flop), 2)]


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


TURN_FIXTURES = """
9s7c3h Kh BW K+FDP | Js8d3h Qs BW Q+FDP
JdJcQc 5c FC | Kh9c6h Jh FC | 3cAcTs Jc FC
9c6hKd 8c SC+FDP | 6h4cKs 5s SC+FDP | 9c8dTs 6d SC+FDP
3s9s9d 9h BP high | 4cTh4d Td BP high+FDP | 6d9cTc Th BP high
KcTd6c Ts BP mid | 8sQs6c 8d BP mid | 4h6c2s 4s BP mid+FDP
Ts2sQc 2d BP low | KhAc5d 5h BP low+FDP | KsQd9d 9s BP low+FDP
5h9c7d Ac BW A+FDP | TcTdQc Ah BW A | 2h8sKd Ac BW A
5s2d8h Kd BW K+FDP | 4d8h2s Kd BW K+FDP | 5h3h9h Kd BW K
5s8h3c Qd BW Q | 2sTs4d Qd BW Q+FDP | 5s8s8c Qh BW Q
6c4h7c Js BW J | 5h4d6h Js BW J | 2d2s2c Jc BW J+FDP
7sJs9h 4h FDP+Brick | Kh9s5s 4h FDP+Brick | 2c2h2s Th FDP+Brick
5c4d8h Td FDP+Brick | 3c6sQc 2s FDP+Brick | 6c5hQd 2h FDP+Brick
7sJh9h Qc SC+BW Q | Kc7cTh Jc FC+SC | 8h3s2h Jh FC+BW J | 8c9dTd Qd FC+SC+BW Q | Qs7hJh Kd SC+BW K
"""
RIVER_FIXTURES = """
AcJhQd2h 7h FC | 9d9cKcAd 6c FC | Jd5h4c7d 9d FC
6d6sAcKd Js SC | Qh3h5c8c 4d SC | 3s9d8s7c 6c SC
Js8hTdQs Qh BP high | 8d2s2c3c 8h BP high | 2cQh5d3c Qd BP high
6h9d7s8s 8h BP mid | 4c7d3hQh 7s BP mid | 7d9hAdTd Ts BP mid
2s8d6s3h 2c BP low | 6c2sKd2h 2c BP low | JhTd2h8d 2s BP low
Qc3sTs8s Ac BW A | 7s2c2hJs Ah BW A | 6d6cTh2d Ac BW A
4hQc6d5s Kd BW K | 7c2s8hJs Kd BW K | 9dJc2c9h Ks BW K
Ts8dTc8h Qs BW Q | 4c2s5dTh Qd BW Q | 5d2s4s8s Qc BW Q
3s2s4c3c Jh BW J | 7c9d5s4h Jc BW J | 6c2d8s8d Js BW J
2s5s3cJh 7d Brick | AsAc9dJd 4s Brick | 3dAh5s4d Kh Brick
"""


def fixtures(text):
    for case in text.replace("\n", " | ").split("|"):
        if case.strip():
            board, card, labels = case.split(maxsplit=2)
            yield board, card, tuple(labels.strip().split("+"))


@pytest.mark.parametrize("board, card, labels", list(fixtures(TURN_FIXTURES)))
def test_turn_examples(board, card, labels):
    assert runout_labels(parse(board), parse(card)[0], "t") == labels


@pytest.mark.parametrize("board, card, labels", list(fixtures(RIVER_FIXTURES)))
def test_river_examples(board, card, labels):
    assert runout_labels(parse(board), parse(card)[0], "r") == labels


def has(board, card, label, street="t"):
    return label in runout_labels(parse(board), parse(card)[0], street)


def test_sc_boundaries():
    assert has("9s7d2c", "8h", "SC") and has("9s7d2c", "Th", "SC")
    assert not has("9s7d2c", "5h", "SC")
    assert has("7s8d9c", "Th", "SC") and not has("7s8d9c", "2h", "SC")
    assert not any(has("Ks8d3c", c, "SC") for c in ("9h", "7h", "6h"))
    assert has("As2d9c", "3h", "SC")
    assert has("AsKd4c", "Jh", "SC")
    assert not has("9s7d2c", "9h", "SC")


def test_bp_boundaries():
    assert has("7s7d2c", "7h", "BP high") and has("7s7d2c", "2h", "BP low")
    assert has("Ks9d6c3h", "9s", "BP mid", "r") and has("Ks9d6c3h", "6s", "BP mid", "r")
    assert has("Ks9d9c", "9h", "BP low")


def test_bw_boundaries():
    assert runout_labels(parse("Ks8d3c"), ("K", "h"), "t") == ("BP high",)
    assert not any(label.startswith("BW") for label in runout_labels(parse("Ts8d3c"), ("T", "h"), "t"))
    assert has("Ks9d6c3h", "Ah", "BW A", "r")
    assert not any(label.startswith("BW") for label in runout_labels(parse("Ks9d6c3h"), ("Q", "h"), "r"))


def test_invariants():
    rng = random.Random(0)
    deck = [rank + suit for rank in "23456789TJQKA" for suit in "cdhs"]
    for street, n in (("t", 3), ("r", 4)):
        for _ in range(20_000):
            *board, card = parse("".join(rng.sample(deck, n + 1)))
            labels = runout_labels(board, card, street)
            made = [label for label in labels if label not in ("FDP", "Brick")]
            assert ("Brick" in labels) == (not made)
            assert sum(label.startswith("BP") for label in labels) <= 1
            assert sum(label.startswith("BW") for label in labels) <= 1
            assert not (street == "r" and "FDP" in labels)
            assert not (any(lab.startswith("BW") for lab in labels) and any(lab.startswith("BP") for lab in labels))


def test_runout_registries():
    assert TURN_LABELS == ("FC", "SC", "BP high", "BP mid", "BP low", "BW A", "BW K", "BW Q", "BW J", "FDP", "Brick")
    assert RIVER_LABELS == tuple(label for label in TURN_LABELS if label != "FDP")


def test_runout_ids_decode():
    assert turn_labels(52, 51, 50, 49) == ("FC", "SC")
    with pytest.raises(ValueError):
        river_labels(1, 2, 3, 4, 0)
