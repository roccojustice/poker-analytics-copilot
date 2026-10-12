import re

STREETS = ("f", "t", "r")
STREET_NAMES = {"f": "flop", "t": "turn", "r": "river"}
LETTERS = set("XBCRF")


class SpotInputError(ValueError):
    pass


def _split_tokens(line, role, position):
    if role not in ("pfr", "pfc"):
        raise SpotInputError(f"Unknown role: {role}")
    if position not in ("ip", "oop"):
        raise SpotInputError(f"Unknown position: {position}")

    text = re.sub(r"\s+", "", line or "").upper()
    if not text:
        raise SpotInputError("Line is empty")

    if role == "pfr":
        if not text.startswith("-"):
            raise SpotInputError("With PFR the Line starts with '-' (your letters)")
        body = text[1:]
    else:
        if not text.startswith("VS"):
            raise SpotInputError("With PFC the Line starts with 'vs' (the villain's letters)")
        body = text[2:]

    if "?" not in body:
        raise SpotInputError("Missing '?': mark where Hero's decision is measured")
    if body.count("?") > 1 or not body.endswith("?"):
        raise SpotInputError("'?' must appear once, at the end of the Line")

    tokens = body[:-1].split("-")
    if len(tokens) > 3:
        raise SpotInputError("A Line has at most 3 streets (flop, turn, river)")

    for street, letters in zip(STREETS, tokens):
        name = STREET_NAMES[street]
        is_decision = street == STREETS[len(tokens) - 1]
        if not letters and not is_decision:
            raise SpotInputError(f"{name}: empty street")
        unknown = sorted(set(letters) - LETTERS)
        if unknown:
            raise SpotInputError(f"{name}: unknown letter '{unknown[0]}' (use X B C R F)")
    return tokens


def parse_line(line, role, position):
    _split_tokens(line, role, position)
    return None
