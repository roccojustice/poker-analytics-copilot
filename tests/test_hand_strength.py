import random

import pytest

from hand_strength import HAND_GROUPS, HAND_TYPES, classify_hand, hand_type

# (hole, flop, type): the spec's user-confirmed table, rank-only rows given rainbow suits
USER_EXAMPLES = [
    ("Kh9s", "JsJd9h", "2nd pair Gk"),
    ("TcTd", "JsJd9h", "2nd pair PP"),
    ("7c7d", "JsJd9h", "Underpair"),
    ("2c2h", "JsJd9h", "Underpair"),
    ("AhKc", "QsQd5h", "Ace high"),
    ("Ah5c", "Ts5s5d", "Trips Tk"),
    ("5c5h", "As2d5s", "Middle set"),
    ("AcAh", "5s5d5h", "Full house"),
    ("AhKc", "QsQdQc", "Ace high"),
    ("KhTc", "9s9d9c", "No made hand"),
    ("7c7d", "Ks5h2s", "2nd pair PP"),
    ("QcQd", "Ks9h2s", "2nd pair PP"),
    ("JcJd", "Ks9h2s", "2nd pair PP"),
    ("TcTd", "Ks9h2s", "2nd pair PP"),
    ("Ac9d", "Ks9h2s", "2nd pair Tk"),
    ("8c8d", "Ks9h3s", "3rd pair"),
    ("4c4d", "Ks9h3s", "3rd pair"),
    ("Ac3d", "Ks9h3s", "3rd pair"),
    ("2c2d", "Ks9h3s", "Underpair"),
    ("QcJd", "As7h2s", "No made hand"),
    ("6h5h", "KhQh6s", "3rd pair"),
    ("JcTd", "ThJs3s", "Top two"),
    ("AcTd", "Th5sAs", "Top two"),
    ("QcJd", "Qs7h3s", "Top pair Gk"),
    ("9c9d", "Ts8h2s", "2nd pair PP"),
    ("6c6d", "Ts8h2s", "3rd pair"),
    ("Ac2d", "Ks9h2s", "3rd pair"),
    ("TcTd", "QsQh6s", "2nd pair PP"),
    ("4c4d", "QsQh6s", "Underpair"),
    ("AcAd", "KsKh3s", "Overpair"),
    ("Ac8d", "8s7h7s", "Top pair Tk"),
    ("Kc9d", "KsKh9s", "Full house"),
    ("9c8d", "9s8hKs", "Bottom two"),
    ("KcQd", "AsJhTs", "Straight"),
    # extra cases from the rules, accepted by the user
    ("9c9d", "JsJh9s", "Full house"),
    ("AcQd", "QsQh5s", "Trips Tk"),
    ("5c5d", "5s5hTs", "Quads"),
    ("AhKh", "Qh7h2h", "Nut flush"),
    ("Ac5d", "4s3h2s", "Straight"),
]


def parse(cards):
    return [(cards[i], cards[i + 1]) for i in range(0, len(cards), 2)]


@pytest.mark.parametrize("hole, flop, type_", USER_EXAMPLES)
def test_user_examples(hole, flop, type_):
    assert classify_hand(parse(hole), parse(flop)) == type_


def test_registry_order():
    assert HAND_TYPES == ("Straight flush", "Quads", "Full house", "Nut flush", "Other flush", "Straight",
                          "Top set", "Middle set", "Bottom set", "Trips Tk", "Trips Gk", "Trips Nk",
                          "Top two", "Top + other", "Bottom two", "Overpair",
                          "Top pair Tk", "Top pair Gk", "Top pair Nk", "2nd pair Tk", "2nd pair Gk", "2nd pair Nk",
                          "2nd pair PP", "3rd pair", "4th pair", "Underpair", "Ace high", "No made hand")
    assert HAND_GROUPS == {
        "Flush": ("Nut flush", "Other flush"),
        "Set": ("Top set", "Middle set", "Bottom set"),
        "Trips": ("Trips Tk", "Trips Gk", "Trips Nk"),
        "Two pair": ("Top two", "Top + other", "Bottom two"),
        "Top pair": ("Top pair Tk", "Top pair Gk", "Top pair Nk"),
        "2nd pair": ("2nd pair Tk", "2nd pair Gk", "2nd pair Nk", "2nd pair PP"),
    }


@pytest.mark.parametrize("hole, flop, type_", [
    ("AhKh", "QhJhTh", "Straight flush"),
    ("5h4h", "3h2hAh", "Straight flush"),
    ("AsAd", "AhAc2s", "Quads"),
    ("Ad2c", "AhAcAs", "Quads"),
    ("AhQh", "QdJh2h", "Top pair Tk"),
    ("Ah5c", "4d3s2h", "Straight"),
    ("KcQd", "AhJsTd", "Straight"),
    ("AcKd", "QhJs9d", "Ace high"),
    ("KcQd", "Ah7s2d", "No made hand"),
])
def test_priority_and_boundaries(hole, flop, type_):
    assert classify_hand(parse(hole), parse(flop)) == type_


@pytest.mark.parametrize("board_size", [3, 4, 5])
def test_invariant_one_type_per_sample(board_size):
    deck = [(rank, suit) for rank in "23456789TJQKA" for suit in "cdhs"]
    rng = random.Random(64)
    for _ in range(20_000):
        cards = rng.sample(deck, 2 + board_size)
        assert classify_hand(cards[:2], cards[2:]) in HAND_TYPES


def card_id(card):
    return "cdhs".index(card[1]) * 13 + "23456789TJQKA".index(card[0]) + 1


def test_hand_type_decodes_pt4_ids():
    ids = [card_id(card) for card in ("Kh", "9s", "Js", "Jd", "9h")]
    assert hand_type(*ids) == "2nd pair Gk"


# (hole, board, type): the turn/river spec's examples
TURN_RIVER_EXAMPLES = [
    ("5c2h", "KsKd5d2s", "2nd pair Nk"),
    ("5c2h", "KsKd5d5s", "Full house"),
    ("3c3h", "KsKd5d5s", "No made hand"),
    ("AcQh", "KsKd5d5s", "Ace high"),
    ("7c7h", "KsKd5d5s", "2nd pair PP"),
    ("Kc5h", "2s2dKd5s", "Top two"),
    ("6c6h", "KsKd5d5s9h", "3rd pair"),
    ("Tc2d", "5h6s7d8c9h", "Straight"),
    ("4c2d", "5h6s7d8c9h", "No made hand"),
    ("AcAd", "5h6s7d8c9h", "No made hand"),
    ("9c9d", "5h6s7d8c9h", "No made hand"),
    ("3s4d", "KsTs7s5s2s", "Other flush"),
    ("2s4d", "AsKsQsJs9s", "No made hand"),
    ("Ac2d", "Kh9s5d2c", "4th pair"),
    ("3c3h", "Kh9s5d2c", "4th pair"),
    ("2c2h", "Kh9s5d3c", "Underpair"),
    ("Ac3d", "Kh9s5d3c2h", "4th pair"),
    ("Ac2d", "Kh9s5d3c2h", "4th pair"),
    ("4c4h", "Kh9s5d3c2h", "4th pair"),
    ("Ac7d", "KsKdKhKc", "Ace high"),
    ("Ac7d", "KsKdKhKc2h", "Ace high"),
    ("Qc7d", "KsKdKhKc2h", "No made hand"),
    ("Ac3d", "KsKd5d5s3h", "Ace high"),
    ("Ah7d", "KsKdKhKcAs", "No made hand"),
    ("3c3h", "KsKdKh5d5s", "No made hand"),
    ("5c2h", "KsKdKh5d5s", "No made hand"),
    ("6c6h", "KsKdKh5d5s", "Full house"),
    ("AcAh", "KsKdKh5d5s", "Full house"),
    ("Kc2h", "KsKdKh5d5s", "Quads"),
]


@pytest.mark.parametrize("hole, board, type_", TURN_RIVER_EXAMPLES)
def test_turn_river_examples(hole, board, type_):
    assert classify_hand(parse(hole), parse(board)) == type_


def test_hand_type_takes_four_and_five_board_ids():
    assert hand_type(*[card_id(c) for c in ("Ac", "2d", "Kh", "9s", "5d", "2c")]) == "4th pair"
    assert hand_type(*[card_id(c) for c in ("Tc", "2d", "5h", "6s", "7d", "8c", "9h")]) == "Straight"


# (hole, board, type): the nut flush spec's examples; the highest suited hole card decides
NUT_FLUSH_EXAMPLES = [
    ("AhTh", "Kh9h4h", "Nut flush"),
    ("KhTh", "Ah9h4h", "Nut flush"),
    ("QhJh", "AhKh7h", "Nut flush"),
    ("QhTh", "Ah9h4h", "Other flush"),
    ("KhQh", "9h7h4h", "Other flush"),
    ("Kh2h", "Ah9h4h", "Nut flush"),
    ("Ah2c", "Kh9h4h3h", "Nut flush"),
    ("Kh2c", "Qh9h4h2h", "Other flush"),
    ("As4d", "KsTs7s5s2s", "Nut flush"),
    ("3s4d", "KsTs7s5s2s", "Other flush"),
    ("2s4d", "AsKsQsJs9s", "No made hand"),
    ("9h8h", "Th7h6h", "Straight flush"),
]


@pytest.mark.parametrize("hole, board, type_", NUT_FLUSH_EXAMPLES)
def test_nut_flush(hole, board, type_):
    assert classify_hand(parse(hole), parse(board)) == type_


# (hole, board, type): the subcategories spec's examples; kicker = place among the ranks off the board
SUBCATEGORY_EXAMPLES = [
    ("KcKd", "Ks7h2d", "Top set"),
    ("7c7d", "Ks7h2d", "Middle set"),
    ("2c2h", "Ks7h2d", "Bottom set"),
    ("7c7d", "KsTh7h2d", "Middle set"),
    ("TcTd", "KsTh7h2d", "Middle set"),
    ("AcKd", "KsKh5d", "Trips Tk"),
    ("KcQd", "KsKh5d", "Trips Gk"),
    ("KcJd", "KsKh5d", "Trips Gk"),
    ("KcTd", "KsKh5d", "Trips Nk"),
    ("KcTd", "KsTh2d", "Top two"),
    ("Kc2h", "KsTh2d", "Top + other"),
    ("Tc2h", "KsTh2d", "Bottom two"),
    ("AcKd", "Ks7h2d", "Top pair Tk"),
    ("KcQd", "Ks7h2d", "Top pair Gk"),
    ("KcJd", "Ks7h2d", "Top pair Gk"),
    ("KcTd", "Ks7h2d", "Top pair Nk"),
    ("AcTd", "KsTh5d", "2nd pair Tk"),
    ("Kc9d", "As9h5d", "2nd pair Tk"),
    ("QcKd", "AsQh5d", "2nd pair Tk"),
    ("Qc8d", "Ks8h5d", "2nd pair Gk"),
    ("Jc8d", "Ks8h5d", "2nd pair Gk"),
    ("Tc8d", "Ks8h5d", "2nd pair Nk"),
    ("8c8d", "As7h3d", "2nd pair PP"),
    ("Kc5h", "KsQhQd9c5d", "Top pair Nk"),
]


@pytest.mark.parametrize("hole, board, type_", SUBCATEGORY_EXAMPLES)
def test_subcategories(hole, board, type_):
    assert classify_hand(parse(hole), parse(board)) == type_
