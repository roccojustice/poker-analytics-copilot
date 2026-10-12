import pytest
from line_parser import parse_line, SpotInputError


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
