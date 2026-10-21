import random

import pytest

from hand_strength import HAND_TYPES, classify_hand, hand_type

# (hole, flop, type): the spec's user-confirmed table, rank-only rows given rainbow suits
USER_EXAMPLES = [
    ("Kh9s", "JsJd9h", "2nd pair"),
    ("TcTd", "JsJd9h", "2nd pair"),
    ("7c7d", "JsJd9h", "Underpair"),
    ("2c2h", "JsJd9h", "Underpair"),
    ("AhKc", "QsQd5h", "Ace high"),
    ("Ah5c", "Ts5s5d", "Trips"),
    ("5c5h", "As2d5s", "Set"),
    ("AcAh", "5s5d5h", "Full house"),
    ("AhKc", "QsQdQc", "Ace high"),
    ("KhTc", "9s9d9c", "No made hand"),
    ("7c7d", "Ks5h2s", "2nd pair"),
    ("QcQd", "Ks9h2s", "2nd pair"),
    ("JcJd", "Ks9h2s", "2nd pair"),
    ("TcTd", "Ks9h2s", "2nd pair"),
    ("Ac9d", "Ks9h2s", "2nd pair"),
    ("8c8d", "Ks9h3s", "3rd pair"),
    ("4c4d", "Ks9h3s", "3rd pair"),
    ("Ac3d", "Ks9h3s", "3rd pair"),
    ("2c2d", "Ks9h3s", "Underpair"),
    ("QcJd", "As7h2s", "No made hand"),
    ("6h5h", "KhQh6s", "3rd pair"),
    ("JcTd", "ThJs3s", "Two pair"),
    ("AcTd", "Th5sAs", "Two pair"),
    ("QcJd", "Qs7h3s", "Top pair"),
    ("9c9d", "Ts8h2s", "2nd pair"),
    ("6c6d", "Ts8h2s", "3rd pair"),
    ("Ac2d", "Ks9h2s", "3rd pair"),
    ("TcTd", "QsQh6s", "2nd pair"),
    ("4c4d", "QsQh6s", "Underpair"),
    ("AcAd", "KsKh3s", "Overpair"),
    ("Ac8d", "8s7h7s", "Top pair"),
    ("Kc9d", "KsKh9s", "Full house"),
    ("9c8d", "9s8hKs", "Two pair"),
    ("KcQd", "AsJhTs", "Straight"),
    # extra cases from the rules, accepted by the user
    ("9c9d", "JsJh9s", "Full house"),
    ("AcQd", "QsQh5s", "Trips"),
    ("5c5d", "5s5hTs", "Quads"),
    ("AhKh", "Qh7h2h", "Flush"),
    ("Ac5d", "4s3h2s", "Straight"),
]


def parse(cards):
    return [(cards[i], cards[i + 1]) for i in range(0, len(cards), 2)]


@pytest.mark.parametrize("hole, flop, type_", USER_EXAMPLES)
def test_user_examples(hole, flop, type_):
    assert classify_hand(parse(hole), parse(flop)) == type_


def test_registry_order():
    assert HAND_TYPES == ("Straight flush", "Quads", "Full house", "Flush", "Straight", "Set", "Trips",
                          "Two pair", "Overpair", "Top pair", "2nd pair", "3rd pair", "Underpair",
                          "Ace high", "No made hand")


@pytest.mark.parametrize("hole, flop, type_", [
    ("AhKh", "QhJhTh", "Straight flush"),
    ("5h4h", "3h2hAh", "Straight flush"),
    ("AsAd", "AhAc2s", "Quads"),
    ("Ad2c", "AhAcAs", "Quads"),
    ("AhQh", "QdJh2h", "Top pair"),
    ("Ah5c", "4d3s2h", "Straight"),
    ("KcQd", "AhJsTd", "Straight"),
    ("AcKd", "QhJs9d", "Ace high"),
    ("KcQd", "Ah7s2d", "No made hand"),
])
def test_priority_and_boundaries(hole, flop, type_):
    assert classify_hand(parse(hole), parse(flop)) == type_


def test_invariant_one_type_per_sample():
    deck = [(rank, suit) for rank in "23456789TJQKA" for suit in "cdhs"]
    rng = random.Random(64)
    for _ in range(20_000):
        cards = rng.sample(deck, 5)
        assert classify_hand(cards[:2], cards[2:]) in HAND_TYPES


def card_id(card):
    return "cdhs".index(card[1]) * 13 + "23456789TJQKA".index(card[0]) + 1


def test_hand_type_decodes_pt4_ids():
    ids = [card_id(card) for card in ("Kh", "9s", "Js", "Jd", "9h")]
    assert hand_type(*ids) == "2nd pair"
