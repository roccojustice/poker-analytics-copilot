import pytest
from line_parser import parse_line, SpotInputError, StreetSpec, LineSpec

BX = ("B", "X")
FCR = ("F", "C", "R")

USER_LIST = {
    ("2bp", "ip", "pfr"): "X XR D XC-X XC-XR XR-B XR-X XC-XC-X XC-XR-B XC-X-X XC-X-B",
    ("2bp", "ip", "pfc"): "B X XR B-B B-X XC-X XR-B B-B-B B-XC-X XC-X-B B-X-B B-X-X XC-XC-X XC-X-X",
    ("2bp", "oop", "pfr"): "Strat B X BC B-B X-C B-C B-B-B B-X BC-X X-X",
    ("2bp", "oop", "pfc"): "B X BC B-B X-C BC-C B-B-B B-X BC-X X-X",
    ("3bp", "ip", "pfr"): "X XR D XC-X X-B XR-B XR-X XC-D XC-XC-X XC-XC-XR XC-X-B XC-X-X XR-B-X XC-XC-D",
    ("3bp", "ip", "pfc"): "B X B-B B-X X-X X-B B-B-B B-B-X B-XC-X B-X-X B-X-B X-XC-X X-B-B X-X-B X-X-X",
    ("3bp", "oop", "pfr"): "Strat R X C C-B R-B C-C C-X X-X X-C B-X R-X C-B-B C-X-B C-C-B",
    ("3bp", "oop", "pfc"): "B X BC B-B X-C BC-C B-B-B B-X BC-X X-X",
}


def S(street, hero, villain):
    return StreetSpec(street, hero, villain)


def SZ(street, hero, villain, size):
    return StreetSpec(street, hero, villain, size)


def streets(spec):
    return [(s.hero, s.villain, s.size) for s in spec.completed + (spec.decision,)]


@pytest.mark.parametrize("line, role, position, message", [
    ("", "pfr", "ip", "Line is empty"),
    ("   ", "pfr", "ip", "Line is empty"),
    ("vs", "pfc", "oop", "Line is empty"),
    ("vs B?", "pfc", "oop", "no '\\?'"),
    ("vs B-X-?", "pfc", "oop", "no '\\?'"),
    ("- B", "pfr", "ip", "villain's actions"),
    ("- B-?", "pfr", "ip", "no '\\?'"),
    ("XC-", "pfr", "ip", "turn: empty street"),
    ("XC--X", "pfr", "ip", "turn: empty street"),
    ("XC", "pfr", "ip", "villain acts next"),
    ("XC-XC", "pfr", "ip", "villain acts next"),
    ("C-C-C", "pfr", "oop", "no street left"),
    ("Strat", "pfr", "ip", "OOP PFR"),
    ("strat", "pfc", "oop", "OOP PFR"),
    ("vs STRAT", "pfc", "ip", "OOP PFR"),
    ("XR-D", "pfr", "ip", "turn: not a donk"),
    ("X-D", "pfr", "ip", "turn: not a donk"),
    ("XC-X-D", "pfr", "ip", "river: not a donk"),
    ("D", "pfc", "ip", "flop: not a donk"),
    ("D", "pfr", "oop", "flop: not a donk"),
    ("C-D", "pfr", "oop", "turn: not a donk"),
    ("XD", "pfr", "ip", "flop: D goes first"),
    ("XC-X-X-X", "pfr", "ip", "at most 3 streets"),
    ("Z", "pfr", "ip", "flop: unknown letter 'Z'"),
    ("B-Z", "pfc", "ip", "turn: unknown letter 'Z'"),
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
        parse_line("X", role, position)


def test_spot_input_error_is_a_value_error():
    assert issubclass(SpotInputError, ValueError)


@pytest.mark.parametrize("line, role, position, expected", [
    # Pre-river
    ("B", "pfc", "ip", LineSpec((), S("f", "", "B"), FCR)),                       # P1, P9
    ("B", "pfc", "oop", LineSpec((), S("f", "X", "B"), FCR)),                     # P2, P8
    ("XC-X", "pfr", "ip", LineSpec((S("f", "B", "XC"),), S("t", "", "X"), BX)),   # P3, P7
    ("C", "pfr", "oop", LineSpec((S("f", "B", "C"),), S("t", "", ""), BX)),       # P4, P5
    ("B-B", "pfc", "ip", LineSpec((S("f", "C", "B"),), S("t", "", "B"), FCR)),    # P6
    ("X", "pfc", "ip", LineSpec((), S("f", "", "X"), BX)),                        # P10
    # River
    ("C-C", "pfr", "oop",
     LineSpec((S("f", "B", "C"), S("t", "B", "C")), S("r", "", ""), BX)),         # R1
    ("XC-XC-X", "pfr", "ip",
     LineSpec((S("f", "B", "XC"), S("t", "B", "XC")), S("r", "", "X"), BX)),      # R2, R7
    ("C-X", "pfr", "oop",
     LineSpec((S("f", "B", "C"), S("t", "X", "X")), S("r", "", ""), BX)),         # R3
    ("B-X", "pfc", "oop",
     LineSpec((S("f", "XC", "B"), S("t", "X", "X")), S("r", "", ""), BX)),        # R4, R8
    ("X-C", "pfc", "oop",
     LineSpec((S("f", "X", "X"), S("t", "B", "C")), S("r", "", ""), BX)),         # R5
    ("X-C", "pfr", "oop",
     LineSpec((S("f", "X", "X"), S("t", "B", "C")), S("r", "", ""), BX)),         # R6
    ("X-XC-X", "pfr", "ip",
     LineSpec((S("f", "X", "X"), S("t", "B", "XC")), S("r", "", "X"), BX)),       # R9
    ("B-XC-X", "pfc", "ip",
     LineSpec((S("f", "C", "B"), S("t", "B", "XC")), S("r", "", "X"), BX)),       # R10
    # Decisions after Hero already acted on the street
    ("C-R", "pfr", "oop", LineSpec((S("f", "B", "C"),), S("t", "B", "R"), FCR)),
    ("XC-XR", "pfr", "ip", LineSpec((S("f", "B", "XC"),), S("t", "B", "XR"), FCR)),
    ("B", "pfr", "oop", LineSpec((), S("f", "X", "B"), FCR)),
    ("Strat", "pfr", "oop", LineSpec((), S("f", "", ""), BX)),
    # The M6 spots: the villain bets first with Hero PFR and IP
    ("XR-B", "pfr", "ip", LineSpec((S("f", "BC", "XR"),), S("t", "", "B"), FCR)),
    ("X-B", "pfr", "ip", LineSpec((S("f", "X", "X"),), S("t", "", "B"), FCR)),
])
def test_valid_line_resolves(line, role, position, expected):
    assert parse_line(line, role, position) == expected


@pytest.mark.parametrize("line, role, position, expected", [
    ("Rs", "pfr", "oop", [("B", "R", "S")]),
    ("XRs-B", "pfr", "ip", [("BC", "XR", "S"), ("", "B", None)]),
    ("XRs-Bl", "pfr", "ip", [("BC", "XR", "S"), ("", "B", "L")]),
    ("XRl", "pfr", "ip", [("B", "XR", "L")]),
    ("XCs-X", "pfr", "ip", [("B", "XC", "S"), ("", "X", None)]),
    ("Bs", "pfc", "oop", [("X", "B", "S")]),
    ("B", "pfc", "oop", [("X", "B", None)]),
    ("D", "pfr", "ip", [("", "B", None)]),
    ("XC-D", "pfr", "ip", [("B", "XC", None), ("", "B", None)]),
    ("XC-Ds", "pfr", "ip", [("B", "XC", None), ("", "B", "S")]),
    ("XC-D", "pfc", "ip", [("B", "XC", None), ("", "B", None)]),
    ("X-B", "pfr", "ip", [("X", "X", None), ("", "B", None)]),
])
def test_confirmed_examples(line, role, position, expected):
    assert streets(parse_line(line, role, position)) == expected


@pytest.mark.parametrize("line, role, position, measured", [
    ("Rs", "pfr", "oop", FCR),
    ("XCs-X", "pfr", "ip", BX),
    ("XC-D", "pfr", "ip", FCR),
    ("C", "pfr", "oop", BX),
])
def test_measured_set(line, role, position, measured):
    assert parse_line(line, role, position).measured == measured


@pytest.mark.parametrize("line, role, donk", [
    ("D", "pfr", True),
    ("XC-D", "pfr", True),
    ("XC-B", "pfr", True),
    ("XC-XC-D", "pfr", True),
    ("B", "pfc", False),
    ("XR-B", "pfr", False),
    ("X-B", "pfr", False),
    ("XC-X-B", "pfr", False),
])
def test_donk_flag_on_the_decision_street(line, role, donk):
    assert parse_line(line, role, "ip").decision.donk is donk


def test_d_and_b_resolve_the_same_streets():
    assert streets(parse_line("XC-D", "pfr", "ip")) == streets(parse_line("XC-B", "pfr", "ip"))


def test_donk_called_on_a_completed_street():
    assert parse_line("XC-D-X", "pfr", "ip").completed[1] == StreetSpec("t", "C", "B", None, True)


@pytest.mark.parametrize("variant", ["vs xrs-b", "XRs - B", "VS XRS-B", " vs  x r s - b "])
def test_case_whitespace_and_vs_are_ignored(variant):
    assert parse_line(variant, "pfr", "ip") == parse_line("XRs-B", "pfr", "ip")


@pytest.mark.parametrize("variant", ["strat", "vs Strat", "STRAT"])
def test_strat_variants(variant):
    assert parse_line(variant, "pfr", "oop") == parse_line("Strat", "pfr", "oop")


@pytest.mark.parametrize("line, role, position, message", [
    ("XX", "pfr", "oop", "flop: 'XX' is impossible heads-up"),
    ("BB-X", "pfr", "oop", "flop: 'BB' is impossible heads-up"),
    ("F", "pfr", "oop", "flop: unknown letter 'F'"),
    ("X", "pfr", "oop", None),
])
def test_impossible_sequences_raise(line, role, position, message):
    if message is None:
        assert parse_line(line, role, position).decision == S("t", "", "")
        return
    with pytest.raises(SpotInputError, match=message):
        parse_line(line, role, position)


@pytest.mark.parametrize("line, role, position, expected", [
    ("Bs", "pfc", "oop", LineSpec((), SZ("f", "X", "B", "S"), FCR)),
    ("XCs-X", "pfc", "ip", LineSpec((SZ("f", "B", "XC", "S"),), S("t", "", "X"), BX)),
    ("BCs", "pfr", "oop", LineSpec((SZ("f", "XR", "BC", "S"),), S("t", "", ""), BX)),
    ("BCl", "pfc", "oop", LineSpec((SZ("f", "XR", "BC", "L"),), S("t", "", ""), BX)),
    ("Bm-XCo-X", "pfc", "ip",
     LineSpec((SZ("f", "C", "B", "M"), SZ("t", "B", "XC", "O")), S("r", "", "X"), BX)),
    ("XCl-X", "pfr", "ip", LineSpec((SZ("f", "B", "XC", "L"),), S("t", "", "X"), BX)),
    ("Cs", "pfr", "oop", LineSpec((SZ("f", "B", "C", "S"),), S("t", "", ""), BX)),
])
def test_size_suffix_sets_the_street_size(line, role, position, expected):
    assert parse_line(line, role, position) == expected


def test_line_without_suffix_has_no_sizes():
    spec = parse_line("B-XC-X", "pfc", "ip")
    assert all(s.size is None for s in spec.completed + (spec.decision,))


@pytest.mark.parametrize("line, role, position, message", [
    ("Xs", "pfr", "ip", "flop: no bet to size"),
    ("Xs-X", "pfr", "oop", "flop: no bet to size"),
    ("B-Xm", "pfc", "oop", "turn: no bet to size"),
    ("Bsm", "pfc", "oop", "flop: the size goes once, at the end of the street's letters"),
    ("XsC", "pfc", "oop", "flop: the size goes once, at the end of the street's letters"),
    ("s", "pfr", "oop", "flop: empty street"),
])
def test_bad_size_suffix_raises(line, role, position, message):
    with pytest.raises(SpotInputError, match=message):
        parse_line(line, role, position)


@pytest.mark.parametrize("key, line", [(key, line) for key, lines in USER_LIST.items() for line in lines.split()])
def test_every_line_of_the_user_list_parses(key, line):
    _, position, role = key
    parse_line(line, role, position)


def test_user_list_has_100_lines():
    assert sum(len(lines.split()) for lines in USER_LIST.values()) == 100
