import pytest

from draws import DRAW_TYPES, classify_draw, draw_parts, draw_type

# (board, hole, type): the spec's table, confirmed by the user in GTO Wizard
GTO_WIZARD_EXAMPLES = [
    ("Jh8h3c", "Ah5h", "Flush draw nuts"),
    ("Jh8h3c", "Kh5h", "Flush draw"),
    ("Jh8h3c", "Th9h", "Combo draw"),
    ("Jh8h3c", "QhTh", "Combo draw"),
    ("Jh8h3c", "Ts9s", "OESD"),
    ("Jh8h3c", "Tc9c", "OESD"),
    ("Jh8h3c", "AcKc", "BDFD 2 cards"),
    ("Jh8h3c", "AhKc", "BDFD 1 card"),
    ("Jh8h3c", "AsKd", "No draw"),
    ("Jh8h3c", "8c7c", "BDFD 2 cards"),
    ("9s8d7c", "Th9h", "OESD"),
    ("9s8d7c", "6h6d", "OESD"),
    ("9s8d7c", "JdTd", "BDFD 2 cards"),
    ("9h7d5c", "Js8d", "OESD"),
    ("Kh8h4h", "Ah5c", "Flush draw nuts"),
    ("Kh8h4h", "QhJc", "Flush draw"),
    ("Kh8h4h", "AcAd", "No draw"),
    ("Ah8h3c", "Kh5h", "Flush draw nuts"),
    ("Jh8h3c2s", "AhKh", "Flush draw nuts"),
    ("Jh8h3c2s", "AcKc", "No draw"),
]

# builder notes and the plan's review focus
EDGE_CASES = [
    ("Jh8h3c2s", "Ah5h", "Combo draw"),  # nut FD + wheel gutshot (the 4)
    ("4h3hKc", "Ah5h", "Combo draw"),  # nut FD + wheel gutshot (the 2)
    ("KhQh4h", "JhTc", "Combo draw"),  # one-card FD + OESD (A or 9)
    ("9s8d7c6h", "2c2d", "No draw"),  # T / 5 make the board's straight
    ("9s8d7c6h", "Th2d", "No draw"),  # made straight
    ("Kh9h5h2h", "Qh3c", "No draw"),  # made flush, no straight out
    ("Kh9h5h2h", "AcQd", "No draw"),  # four-flush board, no heart
    ("8s8dJc", "Td9h", "OESD"),  # paired board, Q or 7
]


def parse(cards):
    return [(cards[i], cards[i + 1]) for i in range(0, len(cards), 2)]


def test_registry_order():
    assert DRAW_TYPES == ("Combo draw", "Flush draw nuts", "Flush draw", "OESD", "Gutshot", "BDFD 2 cards",
                          "BDFD 1 card", "No draw")


@pytest.mark.parametrize("board, hole, type_", GTO_WIZARD_EXAMPLES)
def test_gto_wizard_examples(board, hole, type_):
    assert classify_draw(parse(hole), parse(board)) == type_


@pytest.mark.parametrize("board, hole", [("Jh8h3c2s5d", "AhKh"), ("9s8d7c2h2d", "Th6h")])
def test_river_is_always_no_draw(board, hole):
    assert classify_draw(parse(hole), parse(board)) == "No draw"


@pytest.mark.parametrize("board, hole, type_", EDGE_CASES)
def test_edge_cases(board, hole, type_):
    assert classify_draw(parse(hole), parse(board)) == type_


def test_draw_parts():
    assert draw_parts(parse("Th9h"), parse("Jh8h3c")) == (True, False, 2, 0)
    assert draw_parts(parse("AcKc"), parse("Jh8h3c")) == (False, False, 0, 2)


def card_id(card):
    return "cdhs".index(card[1]) * 13 + "23456789TJQKA".index(card[0]) + 1


def test_draw_type_decodes_card_ids():
    assert draw_type(*(card_id(c) for c in ("Th", "9h", "Jh", "8h", "3c"))) == "Combo draw"


def test_bad_card_id_raises():
    with pytest.raises(ValueError):
        draw_type(0, 5, 1, 2, 3)
