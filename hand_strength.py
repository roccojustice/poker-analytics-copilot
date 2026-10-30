from collections import Counter
from itertools import combinations

from board_types import RANKS
from poker_cards import decode_card_id

# The user's made-hand types, in priority order (page and breakdown order)
HAND_GROUPS = {  # group name -> its types (page and breakdown)
    "Flush": ("Nut flush", "Other flush"),
    "Set": ("Top set", "Middle set", "Bottom set"),
    "Trips": ("Trips Tk", "Trips Gk", "Trips Nk"),
    "Two pair": ("Top two", "Top + other", "Bottom two"),
    "Top pair": ("Top pair Tk", "Top pair Gk", "Top pair Nk"),
    "2nd pair": ("2nd pair Tk", "2nd pair Gk", "2nd pair Nk", "2nd pair PP"),
}
HAND_TYPES = ("Straight flush", "Quads", "Full house", *HAND_GROUPS["Flush"], "Straight", *HAND_GROUPS["Set"],
              *HAND_GROUPS["Trips"], *HAND_GROUPS["Two pair"], "Overpair", *HAND_GROUPS["Top pair"],
              *HAND_GROUPS["2nd pair"], "3rd pair", "4th pair", "Underpair", "Ace high", "No made hand")

PAIR_POSITIONS = ("Top pair", "2nd pair", "3rd pair", "4th pair")
MADE = {8: "Straight flush", 7: "Quads", 6: "Full house", 4: "Straight"}
FLUSH = 5
STRAIGHT = 4


def _value(rank):
    return RANKS.index(rank) + 2


def _straight_high(values):
    values = set(values) | ({1} if 14 in values else set())
    return next((high for high in range(14, 4, -1) if all(high - i in values for i in range(5))), None)


def _rank5(cards):
    """Comparable strength of five cards: (category, tie-break values)."""
    values = sorted((_value(rank) for rank, _ in cards), reverse=True)
    counts = Counter(values)
    ordered = [v for v, n in sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True) for _ in range(n)]
    shape = sorted(counts.values(), reverse=True)
    flush = len({suit for _, suit in cards}) == 1
    high = _straight_high(values) if len(counts) == 5 else None
    if high and flush:
        return (8, high)
    if shape[0] == 4:
        return (7, *ordered)
    if shape == [3, 2]:
        return (6, *ordered)
    if flush:
        return (5, *values)
    if high:
        return (4, high)
    if shape[0] == 3:
        return (3, *ordered)
    return (shape.count(2), *ordered)


def _best(cards):
    return max(_rank5(five) for five in combinations(cards, 5))


def _is_nut(hole, board, suit):
    """Hero's highest hole card of the suit is the highest rank of that suit off the board."""
    on_board = {rank for rank, s in board if s == suit}
    highest = max(_value(rank) for rank, s in hole if s == suit)
    return not any(_value(rank) > highest and rank not in on_board for rank in RANKS)


def _flush_type(hole, board):
    suit = Counter(suit for _, suit in hole + board).most_common(1)[0][0]
    return "Nut flush" if _is_nut(hole, board, suit) else "Other flush"


def _kicker(hole, index, board):
    """Tk / Gk / Nk: hole[index]'s place among the ranks off the board; Nk if it is not in Hero's best five."""
    kicker = hole[index][0]
    off_board = [rank for rank in reversed(RANKS) if rank not in {r for r, _ in board}]
    plays = len(board) == 3 or _best(hole + board) > _best([hole[1 - index]] + board)
    place = off_board.index(kicker) if kicker in off_board and plays else len(off_board)
    return "Tk" if place == 0 else "Gk" if place <= 2 else "Nk"


def _set_type(rank, distinct):
    return "Top set" if rank == distinct[0] else "Bottom set" if rank == distinct[-1] else "Middle set"


def _two_pair_type(ranks, distinct):
    if set(ranks) == set(distinct[:2]):
        return "Top two"
    return "Top + other" if distinct[0] in ranks else "Bottom two"


def classify_hand(hole, board):
    """Hand type of Hero's two (rank, suit) hole cards on a 3-5 card board; the first type that applies wins."""
    best = _best(hole + board)
    if len(board) == 5 and _rank5(board)[0] >= STRAIGHT and best <= _rank5(board):
        return "No made hand"  # the board plays
    h1, h2 = (rank for rank, _ in hole)
    counts = Counter(rank for rank, _ in board)
    if 4 in counts.values():
        return "Ace high" if "A" in (h1, h2) else "No made hand"
    if best[0] == FLUSH:
        return _flush_type(hole, board)
    if best[0] >= STRAIGHT:
        return MADE[best[0]]
    distinct = sorted(counts, key=_value, reverse=True)
    if h1 == h2 and counts[h1] == 1:
        return _set_type(h1, distinct)
    if any(counts[rank] == 2 for rank in (h1, h2)):
        return f"Trips {_kicker(hole, 1 if counts[h1] == 2 else 0, board)}"

    hero_pairs = {h1} if h1 == h2 else {rank for rank in (h1, h2) if counts[rank] == 1}
    board_pairs = {rank for rank, n in counts.items() if n == 2}
    top_two = sorted(hero_pairs | board_pairs, key=_value, reverse=True)[:2]
    playing = sorted((rank for rank in hero_pairs if rank in top_two), key=_value, reverse=True)
    if len(playing) == 2:
        return _two_pair_type(playing, distinct)
    if playing and h1 == h2:
        above = sum(_value(rank) > _value(h1) for rank in distinct)
        if above == 0:
            return "Overpair"
        if above == len(distinct):
            return "Underpair"
        return "2nd pair PP" if above == 1 else PAIR_POSITIONS[min(above, 3)]
    if playing:
        position = PAIR_POSITIONS[min(distinct.index(playing[0]), 3)]
        if position in HAND_GROUPS:
            return f"{position} {_kicker(hole, 1 if playing[0] == h1 else 0, board)}"
        return position
    return "Ace high" if "A" in (h1, h2) else "No made hand"


def hand_type(holecard_1, holecard_2, *board):
    hole = [decode_card_id(int(card)) for card in (holecard_1, holecard_2)]
    return classify_hand(hole, [decode_card_id(int(card)) for card in board])
