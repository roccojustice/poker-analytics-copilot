import re
from dataclasses import dataclass

from sizing import SIZE_BUCKETS

STREETS = ("f", "t", "r")
STREET_NAMES = {"f": "flop", "t": "turn", "r": "river"}
LETTERS = set("XBCRD")


class SpotInputError(ValueError):
    pass


def _split_tokens(line):
    """The villain's letters and size per street; None for Strat."""
    text = re.sub(r"\s+", "", line or "").upper()
    if text.startswith("VS"):
        text = text[2:]
    if not text:
        raise SpotInputError("Line is empty")
    if text == "STRAT":
        return None
    if "?" in text:
        raise SpotInputError("A Line has no '?': it ends at the villain's last action")
    if text.startswith("-"):
        raise SpotInputError("A Line is the villain's actions: no leading '-'")

    tokens = text.split("-")
    if len(tokens) > 3:
        raise SpotInputError("A Line has at most 3 streets (flop, turn, river)")

    parsed = []
    for street, letters in zip(STREETS, tokens):
        name = STREET_NAMES[street]
        size = None
        if letters and letters[-1] in SIZE_BUCKETS:
            letters, size = letters[:-1], letters[-1]
        if any(ch in SIZE_BUCKETS for ch in letters):
            raise SpotInputError(f"{name}: the size goes once, at the end of the street's letters")
        if not letters:
            raise SpotInputError(f"{name}: empty street")
        unknown = sorted(set(letters) - LETTERS)
        if unknown:
            raise SpotInputError(f"{name}: unknown letter '{unknown[0]}' (use X B C R D)")
        if "D" in letters[1:]:
            raise SpotInputError(f"{name}: D goes first on the street")
        parsed.append((letters, size))
    return parsed


@dataclass(frozen=True)
class StreetSpec:
    street: str
    hero: str
    villain: str
    size: str | None = None
    donk: bool = False


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


def _villain_matches(letters, villain_seat):
    return [(seq, closed) for seq, closed in SEQUENCES if seq and _seat_strings(seq)[villain_seat] == letters]


def _resolve(street, letters, is_last, hero_seat):
    """The street's only sequence for the villain's letters: (seq, closed)."""
    villain_seat = 1 - hero_seat
    matches = _villain_matches(letters.replace("D", "B"), villain_seat)
    if is_last:
        ends_on_villain = [(seq, closed) for seq, closed in matches if (len(seq) - 1) % 2 == villain_seat]
        matches = [(seq, closed) for seq, closed in ends_on_villain if not closed or hero_seat == 0]
        if ends_on_villain and not matches:
            raise SpotInputError(f"{STREET_NAMES[street]}: the villain acts next; write his action")
    else:
        matches = [(seq, closed) for seq, closed in matches if closed]
    if len(matches) != 1:
        problem = "is impossible" if not matches else "is ambiguous"
        raise SpotInputError(f"{STREET_NAMES[street]}: '{letters}' {problem} heads-up")
    return matches[0]


def _is_donk(seq, previous, hero_seat, role):
    """The villain bets first and Hero was the last aggressor of the previous street (or preflop)."""
    if hero_seat != 1 or seq[0] != "B":
        return False
    if previous is None:
        return role == "pfr"
    aggressions = [i for i, action in enumerate(previous) if action in "BR"]
    return bool(aggressions) and aggressions[-1] % 2 == hero_seat


def parse_line(line, role, position):
    if role not in ("pfr", "pfc"):
        raise SpotInputError(f"Unknown role: {role}")
    if position not in ("ip", "oop"):
        raise SpotInputError(f"Unknown position: {position}")

    tokens = _split_tokens(line)
    hero_seat = 0 if position == "oop" else 1
    if tokens is None:
        if (role, position) != ("pfr", "oop"):
            raise SpotInputError("Strat is only for OOP PFR")
        return LineSpec((), StreetSpec("f", "", ""), ("B", "X"))

    completed = []
    previous = None
    for index, (letters, size) in enumerate(tokens):
        street = STREETS[index]
        name = STREET_NAMES[street]
        is_last = index == len(tokens) - 1
        seq, closed = _resolve(street, letters, is_last, hero_seat)
        if size and "B" not in seq:
            raise SpotInputError(f"{name}: no bet to size")
        donk = _is_donk(seq, previous, hero_seat, role)
        if letters[0] == "D" and not donk:
            raise SpotInputError(f"{name}: not a donk; write B")
        strings = _seat_strings(seq)
        spec = StreetSpec(street, strings[hero_seat], strings[1 - hero_seat], size, donk)
        if is_last and not closed:
            measured = ("F", "C", "R") if _is_facing(seq) else ("B", "X")
            return LineSpec(tuple(completed), spec, measured)
        completed.append(spec)
        previous = seq

    if len(tokens) == len(STREETS):
        raise SpotInputError("river: no street left to decide on")
    return LineSpec(tuple(completed), StreetSpec(STREETS[len(tokens)], "", ""), ("B", "X"))
