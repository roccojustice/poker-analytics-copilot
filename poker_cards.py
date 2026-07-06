

def decode_card_id(card_id):
    """
    Decode a card ID into its rank and suit.

    Args:
        card_id (int): The ID of the card (1-52).

    Returns:
        tuple: A tuple containing the rank and suit of the card.
    """
    if not 1 <= card_id <= 52:
        raise ValueError("Card ID must be between 1 and 52.")

    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    suits = ['c', 'd', 'h', 's']

    n = card_id - 1
    rank = ranks[n % 13]
    suit = suits[n // 13]

    return rank, suit