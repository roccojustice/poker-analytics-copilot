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
        {"action": "F", "name": "Fold", "hands": 1, "pct": 33.3},
        {"action": "C", "name": "Call", "hands": 2, "pct": 66.7},
        {"action": "R", "name": "Raise", "hands": 0, "pct": 0.0},
    ]


def test_hands_carry_measured_action(monkeypatch):
    install(monkeypatch, fake_matches([(7, "B"), (8, "X")]))
    hands = spotlight.run_spot("2bp", "ip", "pfr", "- B-?")["hands"]
    assert dict(zip(hands["id_hand"], hands["measured_action"])) == {7: "B", 8: "X"}


def test_zero_hands_skips_detail_query_and_returns_empty(monkeypatch):
    calls = install(monkeypatch, fake_matches([]))
    result = spotlight.run_spot("2bp", "ip", "pfr", "- B-?")
    assert calls == []
    assert result["hands"].empty
    assert [row["hands"] for row in result["distribution"]] == [0, 0]
    assert result["interpreted_filter"].endswith("0 hands")


def test_nan_in_hand_details_becomes_none(monkeypatch):
    details = pd.DataFrame({"id_hand": [1], "amt_won": [np.nan]})
    install(monkeypatch, fake_matches([(1, "B")]), details)
    hands = spotlight.run_spot("2bp", "ip", "pfr", "- B-?")["hands"]
    assert hands.to_dict(orient="records") == [{"id_hand": 1, "amt_won": None, "measured_action": "B"}]


def test_describe_reads_like_the_bar():
    spec = parse_line("- B-?", "pfr", "ip")
    text = spotlight.describe("2bp", "ip", "pfr", "BB vs BTN", spec, 1204)
    assert text == "2BP · IP · PFR · BB vs BTN · Flop: Hero B, villain XC · Turn: villain X, measuring B / X · 1,204 hands"


def test_describe_without_formation_says_any():
    spec = parse_line("vs B?", "pfc", "oop")
    text = spotlight.describe("3bp", "oop", "pfc", None, spec, 5)
    assert text == "3BP · OOP · PFC · Any · Flop: Hero X, villain B, measuring F / C / R · 5 hands"
