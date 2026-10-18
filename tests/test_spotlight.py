from datetime import date
import pytest
import numpy as np
import pandas as pd
from line_parser import parse_line
import spotlight


def fake_matches(rows):
    return pd.DataFrame(rows, columns=["id_hand", "measured_action"])


def install(monkeypatch, matches, details=None):
    monkeypatch.setattr("spotlight.run_spot_query", lambda where, params, measured_sql: matches)
    calls = []

    def fake_details(id_hands):
        calls.append(list(id_hands))
        return details if details is not None else pd.DataFrame({"id_hand": list(id_hands)})

    monkeypatch.setattr("spotlight.get_hand_details", fake_details)
    return calls


def test_distribution_counts_in_measured_order_with_zero_rows(monkeypatch):
    install(monkeypatch, fake_matches([(1, "C"), (2, "C"), (3, "F")]))
    result = spotlight.run_spot("2bp", "oop", "pfc", "vs B?")
    assert result["distribution"] == [
        {"action": "F", "label": "XF", "name": "Fold", "hands": 1, "pct": 33.3},
        {"action": "C", "label": "XC", "name": "Call", "hands": 2, "pct": 66.7},
        {"action": "R", "label": "XR", "name": "Raise", "hands": 0, "pct": 0.0},
    ]
    assert all(type(row["pct"]) is float for row in result["distribution"])


def test_hands_carry_the_label(monkeypatch):
    install(monkeypatch, fake_matches([(7, "C"), (8, "F")]))
    hands = spotlight.run_spot("2bp", "oop", "pfc", "vs B?")["hands"]
    assert dict(zip(hands["id_hand"], hands["measured_action"])) == {7: "XC", 8: "XF"}


def test_label_equals_action_without_prefix(monkeypatch):
    install(monkeypatch, fake_matches([(7, "Bs"), (8, "X")]))
    result = spotlight.run_spot("2bp", "ip", "pfr", "- B-?")
    assert [row["label"] for row in result["distribution"]] == ["B", "Bs", "Bm", "Bl", "Bo", "X"]
    assert dict(zip(result["hands"]["id_hand"], result["hands"]["measured_action"])) == {7: "Bs", 8: "X"}


def test_bet_splits_by_size_under_an_overall_row(monkeypatch):
    install(monkeypatch, fake_matches([(1, "Bs"), (2, "Bs"), (3, "Bl"), (4, "X")]))
    rows = spotlight.run_spot("2bp", "ip", "pfr", "- B-?")["distribution"]
    assert rows == [
        {"action": "B", "label": "B", "name": "Bet", "hands": 3, "pct": 75.0},
        {"action": "Bs", "label": "Bs", "name": "Bet small", "hands": 2, "pct": 50.0, "parent": "B"},
        {"action": "Bm", "label": "Bm", "name": "Bet medium", "hands": 0, "pct": 0.0, "parent": "B"},
        {"action": "Bl", "label": "Bl", "name": "Bet large", "hands": 1, "pct": 25.0, "parent": "B"},
        {"action": "Bo", "label": "Bo", "name": "Bet overbet", "hands": 0, "pct": 0.0, "parent": "B"},
        {"action": "X", "label": "X", "name": "Check", "hands": 1, "pct": 25.0},
    ]


def test_bar_values_are_case_insensitive(monkeypatch):
    install(monkeypatch, fake_matches([(1, "C")]))
    result = spotlight.run_spot("2BP", "OOP", "PFC", "vs B?")
    assert result["interpreted_filter"].startswith("2BP · OOP · PFC · Any · ")


def test_duplicate_formations_show_once(monkeypatch):
    install(monkeypatch, fake_matches([(1, "C")]))
    text = spotlight.run_spot("2bp", "oop", "pfc", "vs B?", ["BB vs BTN", "BB vs BTN"])["interpreted_filter"]
    assert "· BB vs BTN · " in text


def test_zero_hands_skips_detail_query_and_returns_empty(monkeypatch):
    calls = install(monkeypatch, fake_matches([]))
    result = spotlight.run_spot("2bp", "ip", "pfr", "- B-?")
    assert calls == []
    assert result["hands"].empty
    assert [row["hands"] for row in result["distribution"]] == [0, 0, 0, 0, 0, 0]
    assert result["interpreted_filter"].endswith("0 hands")


def test_nan_in_hand_details_becomes_none(monkeypatch):
    details = pd.DataFrame({"id_hand": [1], "amt_won": [np.nan]})
    install(monkeypatch, fake_matches([(1, "B")]), details)
    hands = spotlight.run_spot("2bp", "ip", "pfr", "- B-?")["hands"]
    assert hands.to_dict(orient="records") == [{"id_hand": 1, "amt_won": None, "measured_action": "B"}]


def test_describe_reads_like_the_bar():
    spec = parse_line("- B-?", "pfr", "ip")
    text = spotlight.describe("2bp", "ip", "pfr", ["BB vs BTN"], spec, 1204)
    assert text == "2BP · IP · PFR · BB vs BTN · Flop: Hero B, villain XC · Turn: villain X, measuring B / X · 1,204 hands"


def test_describe_without_formation_says_any():
    spec = parse_line("vs B?", "pfc", "oop")
    text = spotlight.describe("3bp", "oop", "pfc", [], spec, 5)
    assert text == "3BP · OOP · PFC · Any · Flop: Hero X, villain B, measuring XF / XC / XR · 5 hands"


def test_describe_joins_several_formations():
    spec = parse_line("vs B?", "pfc", "oop")
    text = spotlight.describe("2bp", "oop", "pfc", ["BB vs BTN", "BB vs CO"], spec, 2668)
    assert text.startswith("2BP · OOP · PFC · BB vs BTN, BB vs CO · Flop: ")


def test_dates_reach_the_query_params(monkeypatch):
    seen = {}

    def fake_query(where, params, measured_sql):
        seen.update(params)
        return fake_matches([(1, "C")])

    install(monkeypatch, fake_matches([]))
    monkeypatch.setattr("spotlight.run_spot_query", fake_query)
    spotlight.run_spot("2bp", "oop", "pfc", "vs B?", [], date(2026, 9, 1), date(2026, 10, 15))
    assert seen.get("date_from") == date(2026, 9, 1)
    assert seen.get("date_to") == date(2026, 10, 16)


@pytest.mark.parametrize("date_from, date_to, shown", [
    (date(2026, 9, 1), date(2026, 10, 15), "2026-09-01 → 2026-10-15"),
    (date(2026, 9, 1), None, "from 2026-09-01"),
    (None, date(2026, 10, 15), "until 2026-10-15"),
])
def test_describe_shows_the_date_range_after_formations(date_from, date_to, shown):
    spec = parse_line("vs B?", "pfc", "oop")
    text = spotlight.describe("2bp", "oop", "pfc", [], spec, 5, date_from, date_to)
    assert text.startswith(f"2BP · OOP · PFC · Any · {shown} · Flop: ")


def test_describe_without_dates_has_no_date_part():
    spec = parse_line("vs B?", "pfc", "oop")
    text = spotlight.describe("2bp", "oop", "pfc", [], spec, 5)
    assert text.startswith("2BP · OOP · PFC · Any · Flop: ")


def test_describe_names_the_size_of_a_completed_street():
    spec = parse_line("vs XCs-X?", "pfc", "ip")
    text = spotlight.describe("2bp", "ip", "pfc", [], spec, 5)
    assert "· Flop: Hero B, villain XC, bet small (<45%) · " in text


def test_describe_names_the_size_on_the_decision_street():
    spec = parse_line("vs Bo?", "pfc", "oop")
    text = spotlight.describe("2bp", "oop", "pfc", [], spec, 5)
    assert "Flop: Hero X, villain B, bet overbet (≥105%), measuring XF / XC / XR" in text


def test_describe_middle_bucket_shows_both_bounds():
    spec = parse_line("vs Bm?", "pfc", "oop")
    assert "bet medium (45–70%)" in spotlight.describe("2bp", "oop", "pfc", [], spec, 5)


@pytest.mark.parametrize("line, expected", [
    ("- ?", "· Flop: measuring B / X · "),
    ("- XRs-?", "· Turn: measuring B / X · "),
])
def test_describe_decision_without_prior_actions_has_no_dangling_comma(line, expected):
    spec = parse_line(line, "pfr", "oop")
    assert expected in spotlight.describe("2bp", "oop", "pfr", [], spec, 5)
