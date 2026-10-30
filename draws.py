from collections import Counter

from board_types import RANKS
from hand_strength import _is_nut, _straight_high, _value
from poker_cards import decode_card_id

# GTO Wizard's draw types, in priority order (page and breakdown order)
DRAW_TYPES = ("Combo draw", "Flush draw nuts", "Flush draw", "OESD", "Gutshot", "BDFD 2 cards", "BDFD 1 card",
              "No draw")
BACKDOORS = {2: "BDFD 2 cards", 1: "BDFD 1 card"}


def _straight(cards):
    return _straight_high([_value(rank) for rank, _ in cards]) or 0


def _out_ranks(hole, board):
    """Ranks whose card gives Hero a straight higher than the board's own; none once Hero has a straight."""
    if _straight(hole + board):
        return 0
    return sum(_straight(hole + board + [(rank, "x")]) > _straight(board + [(rank, "x")]) for rank in RANKS)


def draw_parts(hole, board):
    """(flush draw, nut flush draw, straight out-ranks, backdoor hole cards) on a 3-5 card board."""
    if len(board) == 5:
        return False, False, 0, 0
    counts = Counter(suit for _, suit in hole + board)
    in_hole = Counter(suit for _, suit in hole)
    flush_suit = next((suit for suit, n in counts.items() if n == 4 and in_hole[suit]), None)
    backdoor = 0
    if flush_suit is None and len(board) == 3:
        backdoor = max((in_hole[suit] for suit, n in counts.items() if n == 3), default=0)
    nut = flush_suit is not None and _is_nut(hole, board, flush_suit)
    return flush_suit is not None, nut, _out_ranks(hole, board), backdoor


def classify_draw(hole, board):
    """Draw type of Hero's two (rank, suit) hole cards on a 3-5 card board; the first type that applies wins."""
    flush, nut, outs, backdoor = draw_parts(hole, board)
    if flush and outs:
        return "Combo draw"
    if flush:
        return "Flush draw nuts" if nut else "Flush draw"
    if outs:
        return "OESD" if outs >= 2 else "Gutshot"
    return BACKDOORS.get(backdoor, "No draw")


def draw_type(holecard_1, holecard_2, *board):
    hole = [decode_card_id(int(card)) for card in (holecard_1, holecard_2)]
    return classify_draw(hole, [decode_card_id(int(card)) for card in board])
