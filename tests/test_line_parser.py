import pytest
from line_parser import parse_line, SpotInputError, StreetSpec, LineSpec


@pytest.mark.parametrize("line, role, position, message", [
    ("", "pfr", "ip", "Line is empty"),
    ("   ", "pfr", "ip", "Line is empty"),
    ("vs B?", "pfr", "ip", "With PFR the Line starts with '-'"),
    ("B-?", "pfr", "ip", "With PFR the Line starts with '-'"),
    ("- B?", "pfc", "ip", "With PFC the Line starts with 'vs'"),
    ("B?", "pfc", "oop", "With PFC the Line starts with 'vs'"),
    ("- B-", "pfr", "ip", "Missing '\\?'"),
    ("- ?-B", "pfr", "ip", "'\\?' must appear once, at the end"),
    ("- B?-?", "pfr", "ip", "'\\?' must appear once, at the end"),
    ("- B-B-B-?", "pfr", "oop", "at most 3 streets"),
    ("- -?", "pfr", "oop", "flop: empty street"),
    ("- D?", "pfr", "oop", "flop: unknown letter 'D'"),
    ("vs B-Z?", "pfc", "ip", "turn: unknown letter 'Z'"),
])
def test_invalid_line_raises_with_message(line, role, position, message):
    with pytest.raises(SpotInputError, match=message):
        parse_line(line, role, position)


@pytest.mark.parametrize("role, position, message", [
    ("caller", "ip", "Unknown role: caller"),
    ("pfr", "middle", "Unknown position: middle"),
])
def test_unknown_role_or_position_raises(role, position, message):
    with pytest.raises(SpotInputError, match=message):
        parse_line("- ?", role, position)


def test_spot_input_error_is_a_value_error():
    assert issubclass(SpotInputError, ValueError)

BX = ("B", "X")
FCR = ("F", "C", "R")


def S(street, hero, villain):
    return StreetSpec(street, hero, villain)


@pytest.mark.parametrize("line, role, position, expected", [
    # Pre-river
    ("vs B?", "pfc", "ip", LineSpec((), S("f", "", "B"), FCR)),                      # P1, P9
    ("vs B?", "pfc", "oop", LineSpec((), S("f", "X", "B"), FCR)),                    # P2, P8
    ("- B-?", "pfr", "ip", LineSpec((S("f", "B", "XC"),), S("t", "", "X"), BX)),     # P3, P7
    ("- B-?", "pfr", "oop", LineSpec((S("f", "B", "C"),), S("t", "", ""), BX)),      # P4, P5
    ("vs B-B?", "pfc", "ip", LineSpec((S("f", "C", "B"),), S("t", "", "B"), FCR)),   # P6
    ("vs X?", "pfc", "ip", LineSpec((), S("f", "", "X"), BX)),                       # P10
    # River
    ("- B-B-?", "pfr", "oop",
     LineSpec((S("f", "B", "C"), S("t", "B", "C")), S("r", "", ""), BX)),            # R1
    ("- B-B-?", "pfr", "ip",
     LineSpec((S("f", "B", "XC"), S("t", "B", "XC")), S("r", "", "X"), BX)),         # R2, R7
    ("- B-X-?", "pfr", "oop",
     LineSpec((S("f", "B", "C"), S("t", "X", "X")), S("r", "", ""), BX)),            # R3
    ("vs B-X-?", "pfc", "oop",
     LineSpec((S("f", "XC", "B"), S("t", "X", "X")), S("r", "", ""), BX)),           # R4, R8
    ("vs X-C-?", "pfc", "oop",
     LineSpec((S("f", "X", "X"), S("t", "B", "C")), S("r", "", ""), BX)),            # R5
    ("- X-B-?", "pfr", "oop",
     LineSpec((S("f", "X", "X"), S("t", "B", "C")), S("r", "", ""), BX)),            # R6
    ("- X-B-?", "pfr", "ip",
     LineSpec((S("f", "X", "X"), S("t", "B", "XC")), S("r", "", "X"), BX)),          # R9
    ("vs B-XC-X?", "pfc", "ip",
     LineSpec((S("f", "C", "B"), S("t", "B", "XC")), S("r", "", "X"), BX)),          # R10
    # Decisions after Hero already acted on the street
    ("- B-B?", "pfr", "oop", LineSpec((S("f", "B", "C"),), S("t", "B", "R"), FCR)),
    ("- B-B?", "pfr", "ip", LineSpec((S("f", "B", "XC"),), S("t", "B", "XR"), FCR)),
    ("- X?", "pfr", "oop", LineSpec((), S("f", "X", "B"), FCR)),
    ("- ?", "pfr", "oop", LineSpec((), S("f", "", ""), BX)),
])
def test_valid_line_resolves(line, role, position, expected):
    assert parse_line(line, role, position) == expected


def test_case_and_whitespace_are_ignored():
    assert parse_line(" -  b - ? ", "pfr", "ip") == parse_line("- B-?", "pfr", "ip")


@pytest.mark.parametrize("line, role, position, message", [
    ("- XX-?", "pfr", "oop", "flop: 'XX' is impossible heads-up"),
    ("- BB-?", "pfr", "oop", "flop: 'BB' is impossible heads-up"),
    ("- X?", "pfr", "ip", "flop: 'X' is impossible heads-up"),
    ("- F-?", "pfr", "oop", "flop: 'F' is impossible heads-up"),
    ("vs B-?", "pfc", "ip", "Hero is IP: the villain acts first on the turn"),
    ("vs ?", "pfc", "ip", "Hero is IP: the villain acts first on the flop"),
])
def test_impossible_sequences_raise(line, role, position, message):
    with pytest.raises(SpotInputError, match=message):
        parse_line(line, role, position)
