import re
from dataclasses import dataclass

from sizing import SIZE_BUCKETS

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

    parsed = []
    for street, letters in zip(STREETS, tokens):
        name = STREET_NAMES[street]
        is_decision = street == STREETS[len(tokens) - 1]
        size = None
        if letters and letters[-1] in SIZE_BUCKETS:
            letters, size = letters[:-1], letters[-1]
        if any(ch in SIZE_BUCKETS for ch in letters):
            raise SpotInputError(f"{name}: the size goes once, at the end of the street's letters")
        if not letters and not is_decision:
            raise SpotInputError(f"{name}: empty street")
        unknown = sorted(set(letters) - LETTERS)
        if unknown:
            raise SpotInputError(f"{name}: unknown letter '{unknown[0]}' (use X B C R F)")
        parsed.append((letters, size))
    return parsed


@dataclass(frozen=True)
class StreetSpec:
    street: str
    hero: str
    villain: str
    size: str | None = None


@dataclass(frozen=True)
class LineSpec:
    completed: tuple
    decision: StreetSpec
    measured: tuple


MAX_ACTIONS = 8


def _all_sequences():
    """Every heads-up street sequence as (actions, closed); seat 0 (OOP) acts first."""
    found = []

    def walk(seq, facing, checks):
        found.append((tuple(seq), False))
        if len(seq) >= MAX_ACTIONS:
            return
        for action in (("F", "C", "R") if facing else ("X", "B")):
            if action == "F":
                continue  # a fold ends the hand, so it is never part of a Line
            nxt = seq + [action]
            if action == "C" or (action == "X" and checks == 1):
                found.append((tuple(nxt), True))
            else:
                walk(nxt, action in "BR", checks + (action == "X"))

    walk([], False, 0)
    return found


SEQUENCES = _all_sequences()


def _seat_strings(seq):
    return "".join(seq[0::2]), "".join(seq[1::2])


def _is_facing(seq):
    return bool(seq) and seq[-1] in "BR"


def _resolve(street, letters, is_decision, hero_seat, pfr_seat, role):
    matches = []
    for seq, closed in SEQUENCES:
        if closed == is_decision:
            continue
        if _seat_strings(seq)[pfr_seat] != letters:
            continue
        if is_decision and len(seq) % 2 != hero_seat:
            continue
        matches.append(seq)
    if is_decision and role == "pfr" and letters == "":
        matches = [seq for seq in matches if not _is_facing(seq)]  # no donks in v1
    if len(matches) != 1:
        problem = "is impossible" if not matches else "is ambiguous"
        raise SpotInputError(f"{STREET_NAMES[street]}: '{letters}' {problem} heads-up")
    return matches[0]


def parse_line(line, role, position):
    tokens = _split_tokens(line, role, position)
    hero_seat = 0 if position == "oop" else 1
    pfr_seat = hero_seat if role == "pfr" else 1 - hero_seat

    decision_street = STREETS[len(tokens) - 1]
    if role == "pfc" and hero_seat == 1 and tokens[-1][0] == "":
        raise SpotInputError(
            f"Hero is IP: the villain acts first on the {STREET_NAMES[decision_street]}; "
            "write his action before '?'"
        )

    completed = []
    for street, (letters, size) in zip(STREETS, tokens):
        is_decision = street == decision_street
        seq = _resolve(street, letters, is_decision, hero_seat, pfr_seat, role)
        if size and "B" not in seq:
            raise SpotInputError(f"{STREET_NAMES[street]}: no bet to size")
        strings = _seat_strings(seq)
        spec = StreetSpec(street, strings[hero_seat], strings[1 - hero_seat], size)
        if is_decision:
            measured = ("F", "C", "R") if _is_facing(seq) else ("B", "X")
            return LineSpec(tuple(completed), spec, measured)
        completed.append(spec)
