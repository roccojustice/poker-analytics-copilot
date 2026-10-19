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
