from collections import Counter

from board_types import RANKS
from poker_cards import decode_card_id

# The user's made-hand types, in priority order (page and breakdown order)
HAND_TYPES = ("Straight flush", "Quads", "Full house", "Flush", "Straight", "Set", "Trips", "Two pair",
              "Overpair", "Top pair", "2nd pair", "3rd pair", "Underpair", "Ace high", "No made hand")

PAIR_POSITIONS = ("Top pair", "2nd pair", "3rd pair")


def _value(rank):
    return RANKS.index(rank) + 2


def _is_straight(ranks):
    values = {_value(rank) for rank in ranks}
    if 14 in values:
        values.add(1)
    return any(all(low + step in values for step in range(5)) for low in range(1, 11))


def _flush_ranks(cards):
    suits = Counter(suit for _, suit in cards)
    suit, count = suits.most_common(1)[0]
    return [rank for rank, s in cards if s == suit] if count >= 5 else None


def classify_hand(hole, board):
    """Hand type of Hero's two (rank, suit) hole cards on the board; the first type that applies wins."""
    cards = hole + board
    counts = sorted(Counter(rank for rank, _ in cards).values(), reverse=True)
    flush = _flush_ranks(cards)
    if flush and _is_straight(flush):
        return "Straight flush"
    if counts[0] == 4:
        return "Quads"
    if counts[0] >= 3 and counts[1] >= 2:
        return "Full house"
    if flush:
        return "Flush"
    if _is_straight([rank for rank, _ in cards]):
        return "Straight"

    h1, h2 = (rank for rank, _ in hole)
    board_ranks = [rank for rank, _ in board]
    distinct = sorted(set(board_ranks), key=_value, reverse=True)
    if h1 == h2 and h1 in board_ranks:
        return "Set"
    if any(board_ranks.count(rank) == 2 for rank in (h1, h2)):
        return "Trips"
    if h1 != h2 and h1 in board_ranks and h2 in board_ranks:
        return "Two pair"
    if h1 == h2:
        above = sum(_value(rank) > _value(h1) for rank in distinct)
        if above == 0:
            return "Overpair"
        if above == len(distinct):
            return "Underpair"
        return PAIR_POSITIONS[above]
    paired = [rank for rank in (h1, h2) if rank in board_ranks]
    if paired:
        return PAIR_POSITIONS[distinct.index(paired[0])]
    return "Ace high" if "A" in (h1, h2) else "No made hand"


def hand_type(holecard_1, holecard_2, card_1, card_2, card_3):
    hole = [decode_card_id(int(card)) for card in (holecard_1, holecard_2)]
    board = [decode_card_id(int(card)) for card in (card_1, card_2, card_3)]
    return classify_hand(hole, board)
