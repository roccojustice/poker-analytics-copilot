from itertools import combinations, product

from poker_cards import decode_card_id

# The user's flop taxonomy, most to least common over all flops (page order)
FLOP_TYPES = ("BLL", "Low", "2BWL", "Low paired", "High paired", "A high", "Monotone", "3BW")

RANKS = "23456789TJQKA"
BROADWAY = set("AKQJT")


def classify(cards):
    """Flop type of three (rank, suit) cards; every flop gets exactly one type."""
    ranks = [rank for rank, _ in cards]
    if len({suit for _, suit in cards}) == 1:
        return "Monotone"
    paired = next((r for r in ranks if ranks.count(r) > 1), None)
    if paired:
        return "Low paired" if RANKS.index(paired) <= RANKS.index("8") else "High paired"
    broadway = [r for r in ranks if r in BROADWAY]
    if len(broadway) == 3:
        return "3BW"
    if len(broadway) == 2:
        return "2BWL"
    if broadway == ["A"]:
        return "A high"
    if broadway and broadway[0] in "KQJ":
        return "BLL"
    return "Low"


def flop_type(card_1, card_2, card_3):
    return classify([decode_card_id(int(card)) for card in (card_1, card_2, card_3)])



TURN_LABELS = ("FC", "SC", "BP high", "BP mid", "BP low", "BW A", "BW K", "BW Q", "BW J", "FDP", "Brick")
RIVER_LABELS = tuple(label for label in TURN_LABELS if label != "FDP")


def _values(rank):
    value = RANKS.index(rank) + 2
    return (14, 1) if value == 14 else (value,)


def _closes_straight(previous_ranks, rank):
    """A new rank forming, with two other board ranks, a trio spanning 3 or less (A high or low)."""
    if rank in previous_ranks:
        return False
    for low, high in combinations(sorted(previous_ranks), 2):
        for trio in product(_values(rank), _values(low), _values(high)):
            if len(set(trio)) == 3 and max(trio) - min(trio) <= 3:
                return True
    return False


def runout_labels(previous, card, street):
    """Labels of the turn ("t") or river ("r") card against the previous board, in page order."""
    rank, suit = card
    suited = sum(s == suit for _, s in previous) + 1
    previous_ranks = {r for r, _ in previous}
    board = sorted(previous_ranks, key=RANKS.index)
    labels = set()
    if suited >= 3:
        labels.add("FC")
    if _closes_straight(previous_ranks, rank):
        labels.add("SC")
    if rank in previous_ranks:
        labels.add("BP high" if rank == board[-1] else "BP low" if rank == board[0] else "BP mid")
    elif rank in "AKQJ" and RANKS.index(rank) > RANKS.index(board[-1]):
        labels.add(f"BW {rank}")
    if street == "t" and suited == 2:
        labels.add("FDP")
    if not labels - {"FDP"}:
        labels.add("Brick")
    return tuple(label for label in TURN_LABELS if label in labels)


def _decode(card_ids):
    return [decode_card_id(int(card)) for card in card_ids]


def turn_labels(card_1, card_2, card_3, card_4):
    *previous, card = _decode((card_1, card_2, card_3, card_4))
    return runout_labels(previous, card, "t")


def river_labels(card_1, card_2, card_3, card_4, card_5):
    *previous, card = _decode((card_1, card_2, card_3, card_4, card_5))
    return runout_labels(previous, card, "r")
