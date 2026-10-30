from datetime import date
import pytest
import numpy as np
import pandas as pd
from line_parser import parse_line
from line_parser import SpotInputError
import spotlight

BLL_FLOP = "Ks9d3c"


def card_id(card):
    return "cdhs".index(card[1]) * 13 + "23456789TJQKA".index(card[0]) + 1


def fake_matches(rows):
    """Rows are (id_hand, letter[, flop[, runout[, hole]]]): BLL flop, turn 2h, no river, hole 7h6h by default."""
    records = []
    for row in rows:
        id_hand, letter, flop, runout, hole = [*row, *(BLL_FLOP, "2h", "7h6h")[len(row) - 2:]]
        cards = [card_id(board[i:i + 2]) for board in (flop, runout) for i in range(0, len(board), 2)]
        records.append((id_hand, *cards, *[0] * (5 - len(cards)), card_id(hole[:2]), card_id(hole[2:]), letter))
    columns = ["id_hand", "card_1", "card_2", "card_3", "card_4", "card_5", "holecard_1", "holecard_2",
               "measured_action"]
    return pd.DataFrame(records, columns=columns)


def install(monkeypatch, matches, details=None):
    monkeypatch.setattr("spotlight.run_spot_query", lambda where, params, measured_sql: matches)
    calls = []

    def fake_details(id_hands):
        calls.append(list(id_hands))
        return details if details is not None else pd.DataFrame({"id_hand": list(id_hands)})

    monkeypatch.setattr("spotlight.get_hand_details", fake_details)
    return calls


def test_distribution_counts_in_measured_order_with_zero_rows(monkeypatch):
    install(monkeypatch, fake_matches([(1, "Cs"), (2, "Cm"), (3, "Fs")]))
    result = spotlight.run_spot("2bp", "oop", "pfc", "vs B?")
    assert result["distribution"] == [
        {"action": "F", "label": "XF", "name": "Fold", "hands": 1, "pct": 33.3},
        {"action": "C", "label": "XC", "name": "Call", "hands": 2, "pct": 66.7},
        {"action": "R", "label": "XR", "name": "Raise", "hands": 0, "pct": 0.0},
    ]
    assert all(type(row["pct"]) is float for row in result["distribution"])


def test_hands_carry_the_label(monkeypatch):
    install(monkeypatch, fake_matches([(7, "Cs"), (8, "Fm")]))
    hands = spotlight.run_spot("2bp", "oop", "pfc", "vs B?")["hands"]
    assert dict(zip(hands["id_hand"], hands["measured_action"])) == {7: "XCs", 8: "XFm"}


def test_split_rows_in_bucket_order_with_row_relative_pct(monkeypatch):
    install(monkeypatch, fake_matches([(1, "Fs"), (2, "Cs"), (3, "Cs"), (4, "Rl")]))
    split = spotlight.run_spot("2bp", "oop", "pfc", "vs B?")["split"]
    assert [row["size"] for row in split] == ["S", "M", "L", "O"]
    assert split[0] == {"size": "S", "name": "small", "hands": 3, "pct_faced": 75.0, "cells": [
        {"action": "F", "label": "XFs", "hands": 1, "pct": 33.3},
        {"action": "C", "label": "XCs", "hands": 2, "pct": 66.7},
        {"action": "R", "label": "XRs", "hands": 0, "pct": 0.0},
    ]}
    assert split[1]["hands"] == 0 and [c["pct"] for c in split[1]["cells"]] == [0.0, 0.0, 0.0]
    assert split[2]["pct_faced"] == 25.0 and split[2]["cells"][2]["pct"] == 100.0


def test_split_with_zero_hands_has_four_zero_rows(monkeypatch):
    install(monkeypatch, fake_matches([]))
    split = spotlight.run_spot("2bp", "oop", "pfc", "vs B?")["split"]
    assert [(r["hands"], r["pct_faced"]) for r in split] == [(0, 0.0)] * 4


@pytest.mark.parametrize("line, role, position, rows", [
    ("vs Bs?", "pfc", "oop", [(1, "C")]),
    ("- B-?", "pfr", "ip", [(1, "Bs")]),
])
def test_split_is_none_when_not_applicable(monkeypatch, line, role, position, rows):
    install(monkeypatch, fake_matches(rows))
    assert spotlight.run_spot("2bp", position, role, line)["split"] is None


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
    assert hands.to_dict(orient="records") == [
        {"id_hand": 1, "amt_won": None, "flop_type": "BLL", "turn_type": "Brick", "river_type": None,
         "hand_type": "No made hand", "draw_type": "No draw", "measured_action": "B"}]


MIXED = [(1, "Cs", "KsQd4c"), (2, "Cs", "Ks9d3c"), (3, "Fm", "7s6d2c")]  # 2BWL, BLL, Low


def test_flop_filter_keeps_only_selected_types(monkeypatch):
    install(monkeypatch, fake_matches(MIXED))
    result = spotlight.run_spot("2bp", "oop", "pfc", "vs B?", flop_types=["BLL", "Low"])
    assert set(result["hands"]["id_hand"]) == {2, 3}
    assert [row["hands"] for row in result["distribution"]] == [1, 1, 0]
    assert result["split"][0]["hands"] == 1


def test_no_flop_types_keeps_every_hand(monkeypatch):
    install(monkeypatch, fake_matches(MIXED))
    hands = spotlight.run_spot("2bp", "oop", "pfc", "vs B?")["hands"]
    assert dict(zip(hands["id_hand"], hands["flop_type"])) == {1: "2BWL", 2: "BLL", 3: "Low"}


def test_flop_filter_to_zero_hands(monkeypatch):
    calls = install(monkeypatch, fake_matches(MIXED))
    result = spotlight.run_spot("2bp", "oop", "pfc", "vs B?", flop_types=["Monotone"])
    assert calls == []
    assert [row["hands"] for row in result["distribution"]] == [0, 0, 0]
    assert [row["hands"] for row in result["split"]] == [0, 0, 0, 0]
    assert result["interpreted_filter"].endswith("0 hands")


def test_unknown_flop_type_raises_before_the_query(monkeypatch):
    def no_query(*args):
        raise AssertionError("queried")

    monkeypatch.setattr("spotlight.run_spot_query", no_query)
    with pytest.raises(SpotInputError, match="bll"):
        spotlight.run_spot("2bp", "oop", "pfc", "vs B?", flop_types=["bll"])


def test_duplicate_flop_types_show_once(monkeypatch):
    install(monkeypatch, fake_matches(MIXED))
    text = spotlight.run_spot("2bp", "oop", "pfc", "vs B?", flop_types=["BLL", "BLL"])["interpreted_filter"]
    assert text.count("Flop type: BLL") == 1 and "BLL, BLL" not in text


RUNOUTS = [(1, "Bs", "9s7c3h", "Kh"), (2, "X", "9s7c3h", "8d"), (3, "Bs", "9s7c3h", "2d")]  # BW K+FDP, SC, Brick


def test_turn_filter_or_within_street(monkeypatch):
    install(monkeypatch, fake_matches(RUNOUTS))
    result = spotlight.run_spot("2bp", "ip", "pfr", "- B-?", turn_types=["SC", "BW K"])
    assert set(result["hands"]["id_hand"]) == {1, 2}
    assert [row["hands"] for row in result["distribution"] if "parent" not in row] == [1, 1]


def test_flop_turn_river_and(monkeypatch):
    rows = [(1, "B", BLL_FLOP, "2c7d"),    # BLL, turn FDP+Brick, river Brick
            (2, "B", BLL_FLOP, "2c7c"),    # BLL, turn FDP+Brick, river FC
            (3, "B", BLL_FLOP, "Kc7c"),    # BLL, turn BP high+FDP, river FC
            (4, "B", "7s6d2c", "Ah7c")]    # Low
    install(monkeypatch, fake_matches(rows))
    result = spotlight.run_spot("2bp", "ip", "pfr", "- B-B-?", flop_types=["BLL"], turn_types=["Brick"],
                                river_types=["FC"])
    assert list(result["hands"]["id_hand"]) == [2]


def test_turn_decision_without_river(monkeypatch):
    install(monkeypatch, fake_matches(RUNOUTS))
    hands = spotlight.run_spot("2bp", "ip", "pfr", "- B-?")["hands"]
    assert list(hands["turn_type"]) == ["BW K, FDP", "SC", "Brick"]
    assert list(hands["river_type"]) == [None, None, None]


def test_flop_decision_has_no_runout_values(monkeypatch):
    install(monkeypatch, fake_matches([(1, "Cs", BLL_FLOP, "")]))
    hands = spotlight.run_spot("2bp", "oop", "pfc", "vs B?")["hands"]
    assert hands.loc[0, "turn_type"] is None and hands.loc[0, "river_type"] is None


def no_query(*args):
    raise AssertionError("queried")


@pytest.mark.parametrize("line, kwargs", [
    ("vs B?", {"turn_types": ["FC"]}),
    ("- B-?", {"river_types": ["Brick"]}),
])
def test_runout_types_need_their_street(monkeypatch, line, kwargs):
    monkeypatch.setattr("spotlight.run_spot_query", no_query)
    role, position = ("pfc", "oop") if line.startswith("vs") else ("pfr", "ip")
    with pytest.raises(SpotInputError, match="decision"):
        spotlight.run_spot("2bp", position, role, line, **kwargs)


@pytest.mark.parametrize("kwargs, bad", [({"turn_types": ["fc"]}, "fc"), ({"river_types": ["FDP"]}, "FDP")])
def test_unknown_runout_label_raises(monkeypatch, kwargs, bad):
    monkeypatch.setattr("spotlight.run_spot_query", no_query)
    with pytest.raises(SpotInputError, match=bad):
        spotlight.run_spot("2bp", "ip", "pfr", "- B-B-?", **kwargs)


def test_describe_runout_parts(monkeypatch):
    install(monkeypatch, fake_matches([(1, "Bs", BLL_FLOP, "2c7d")]))
    text = spotlight.run_spot("2bp", "ip", "pfr", "- B-B-?", flop_types=["BLL"], turn_types=["FC", "BP high", "FC"],
                              river_types=["Brick"])["interpreted_filter"]
    assert "· Flop type: BLL · Turn type: FC, BP high · River type: Brick · " in text
    plain = spotlight.run_spot("2bp", "ip", "pfr", "- B-B-?")["interpreted_filter"]
    assert "Turn type" not in plain and "River type" not in plain


def test_hand_columns_joined_in_page_order(monkeypatch):
    install(monkeypatch, fake_matches([(1, "B", "Ts9h8d", "Qc")]))
    hands = spotlight.run_spot("2bp", "ip", "pfr", "- B-?")["hands"]
    assert hands.loc[0, "turn_type"] == "SC, BW Q"


HOLES = [(1, "Cs", BLL_FLOP, "2h", "KcQd"), (2, "Cs", BLL_FLOP, "2h", "9c8c"),  # Top pair Gk, 2nd pair Nk
         (3, "Fs", BLL_FLOP, "2h", "7h6h"), (4, "Cs", "7s6d2c", "2h", "KcQd")]  # No made hand, Low flop K high


def test_hand_filter_or_within(monkeypatch):
    install(monkeypatch, fake_matches(HOLES[:3]))
    hands = spotlight.run_spot("2bp", "oop", "pfc", "vs B?", hand_types=["Top pair Gk", "2nd pair Nk"])["hands"]
    assert dict(zip(hands["id_hand"], hands["hand_type"])) == {1: "Top pair Gk", 2: "2nd pair Nk"}


def test_hand_and_flop_type(monkeypatch):
    install(monkeypatch, fake_matches(HOLES))
    hands = spotlight.run_spot("2bp", "oop", "pfc", "vs B?", flop_types=["BLL"],
                               hand_types=["Top pair Gk", "No made hand"])["hands"]
    assert set(hands["id_hand"]) == {1, 3}


def test_no_hand_types_keeps_every_hand(monkeypatch):
    install(monkeypatch, fake_matches(HOLES))
    hands = spotlight.run_spot("2bp", "oop", "pfc", "vs B?")["hands"]
    assert dict(zip(hands["id_hand"], hands["hand_type"])) == {
        1: "Top pair Gk", 2: "2nd pair Nk", 3: "No made hand", 4: "No made hand"}


def test_hand_types_on_a_turn_decision(monkeypatch):
    install(monkeypatch, fake_matches(RUNOUTS))  # 7h6h: 3rd pair on 9s7c3h + Kh / 8d, 2nd pair Nk + 2d
    hands = spotlight.run_spot("2bp", "ip", "pfr", "- B-?", hand_types=["2nd pair Nk"])["hands"]
    assert list(hands["id_hand"]) == [3]


def test_unknown_hand_type_raises(monkeypatch):
    monkeypatch.setattr("spotlight.run_spot_query", no_query)
    with pytest.raises(SpotInputError, match="Unknown hand type: Monster"):
        spotlight.run_spot("2bp", "oop", "pfc", "vs B?", hand_types=["Monster"])


def test_turn_decision_labels_the_turn_board(monkeypatch):
    install(monkeypatch, fake_matches(RUNOUTS))  # fake rows have card_5 = 0: never read on a turn decision
    hands = spotlight.run_spot("2bp", "ip", "pfr", "- B-?")["hands"]
    assert list(hands["hand_type"]) == ["3rd pair", "3rd pair", "2nd pair Nk"]


def test_river_decision_labels_the_river_board(monkeypatch):
    install(monkeypatch, fake_matches([(1, "B", BLL_FLOP, "2c7d")]))  # 7h6h on Ks9d3c 2c 7d
    hands = spotlight.run_spot("2bp", "ip", "pfr", "- B-B-?")["hands"]
    assert list(hands["hand_type"]) == ["3rd pair"]


def test_hole_cards_not_duplicated_by_details(monkeypatch):
    details = pd.DataFrame({"id_hand": [1], "holecard_1": [5], "holecard_2": [6]})
    install(monkeypatch, fake_matches(HOLES[:1]), details)
    hands = spotlight.run_spot("2bp", "oop", "pfc", "vs B?")["hands"]
    assert [c for c in hands.columns if c.startswith("holecard")] == ["holecard_1", "holecard_2"]


def test_describe_hand_part(monkeypatch):
    install(monkeypatch, fake_matches(HOLES[:1]))
    text = spotlight.run_spot("2bp", "oop", "pfc", "vs B?", flop_types=["BLL"],
                              hand_types=["Top pair Gk", "Overpair", "Top pair Gk"])["interpreted_filter"]
    assert "· Flop type: BLL · Hand: Top pair Gk, Overpair · Flop: " in text
    assert "Hand:" not in spotlight.run_spot("2bp", "oop", "pfc", "vs B?")["interpreted_filter"]


def test_hand_split_rows_cells_and_pcts(monkeypatch):
    install(monkeypatch, fake_matches([(1, "Bs", BLL_FLOP, "2h", "KcQd"), (2, "X", BLL_FLOP, "2h", "KcQd"),
                                       (3, "X", BLL_FLOP, "2h", "7h6h")]))
    split = spotlight.run_spot("2bp", "ip", "pfr", "- ?")["hand_split"]
    assert [(r["hand_type"], r["hands"], r["pct_total"]) for r in split] == [
        ("Top pair", 2, 66.7), ("Top pair Gk", 2, 66.7), ("No made hand", 1, 33.3)]
    assert [(c["label"], c["hands"], c["pct"]) for c in split[0]["cells"]] == [
        ("B", 1, 50.0), ("Bs", 1, 50.0), ("Bm", 0, 0.0), ("Bl", 0, 0.0), ("Bo", 0, 0.0), ("X", 1, 50.0)]


def test_hand_split_facing_uses_unsized_cells(monkeypatch):
    install(monkeypatch, fake_matches(HOLES[:3]))
    split = spotlight.run_spot("2bp", "oop", "pfc", "vs B?")["hand_split"]
    assert [c["label"] for c in split[0]["cells"]] == ["XF", "XC", "XR"]
    assert [(r["hand_type"], [c["hands"] for c in r["cells"]]) for r in split] == [
        ("Top pair", [0, 1, 0]), ("Top pair Gk", [0, 1, 0]), ("2nd pair", [0, 1, 0]), ("2nd pair Nk", [0, 1, 0]),
        ("No made hand", [1, 0, 0])]


def test_hand_split_on_turn_decision(monkeypatch):
    install(monkeypatch, fake_matches(RUNOUTS))
    split = spotlight.run_spot("2bp", "ip", "pfr", "- B-?")["hand_split"]
    assert [(r["hand_type"], r["hands"], r["pct_total"]) for r in split] == [
        ("2nd pair", 1, 33.3), ("2nd pair Nk", 1, 33.3), ("3rd pair", 2, 66.7)]


def test_hand_split_empty_list_when_no_hands(monkeypatch):
    install(monkeypatch, fake_matches(HOLES[:1]))
    assert spotlight.run_spot("2bp", "oop", "pfc", "vs B?", hand_types=["Top set"])["hand_split"] == []


MONOTONE = "Kh9h3h"
FLUSHES = [(1, "Bs", MONOTONE, "2c", "AhQh"), (2, "X", MONOTONE, "2c", "QhJh"),  # Nut flush, Other flush
           (3, "X", MONOTONE, "2c", "8h7h"), (4, "Bs", MONOTONE, "2c", "KcQd")]  # Other flush, Top pair Gk


def split_rows(split):
    return [(r["hand_type"], r["hands"], r["pct_total"], r.get("parent")) for r in split]


def test_hand_split_flush_group_and_leaves(monkeypatch):
    install(monkeypatch, fake_matches(FLUSHES))
    split = spotlight.run_spot("2bp", "ip", "pfr", "- ?")["hand_split"]
    assert split_rows(split) == [("Flush", 3, 75.0, None), ("Nut flush", 1, 25.0, "Flush"),
                                 ("Other flush", 2, 50.0, "Flush"), ("Top pair", 1, 25.0, None),
                                 ("Top pair Gk", 1, 25.0, "Top pair")]
    leaves = [c["hands"] for c in split[1]["cells"]], [c["hands"] for c in split[2]["cells"]]
    assert [c["hands"] for c in split[0]["cells"]] == [a + b for a, b in zip(*leaves)]


def test_hand_split_top_pair_group(monkeypatch):
    install(monkeypatch, fake_matches([(1, "Bs", BLL_FLOP, "2h", "KcQd"), (2, "X", BLL_FLOP, "2h", "AcKd")]))
    split = spotlight.run_spot("2bp", "ip", "pfr", "- ?")["hand_split"]
    assert split_rows(split) == [("Top pair", 2, 100.0, None), ("Top pair Tk", 1, 50.0, "Top pair"),
                                 ("Top pair Gk", 1, 50.0, "Top pair")]


def test_hand_split_flush_group_with_one_leaf(monkeypatch):
    install(monkeypatch, fake_matches(FLUSHES[1:3]))
    split = spotlight.run_spot("2bp", "ip", "pfr", "- ?")["hand_split"]
    assert split_rows(split) == [("Flush", 2, 100.0, None), ("Other flush", 2, 100.0, "Flush")]


def test_flush_group_is_not_a_hand_type_filter(monkeypatch):
    install(monkeypatch, fake_matches(FLUSHES))
    with pytest.raises(SpotInputError, match="Unknown hand type: Flush"):
        spotlight.run_spot("2bp", "ip", "pfr", "- ?", hand_types=["Flush"])


def test_describe_flop_part_after_dates():
    spec = parse_line("vs B?", "pfc", "oop")
    text = spotlight.describe("2bp", "oop", "pfc", [], spec, 5, date(2026, 9, 1), None, ["BLL", "Low"])
    assert "· from 2026-09-01 · Flop type: BLL, Low · " in text
    assert "Flop type" not in spotlight.describe("2bp", "oop", "pfc", [], spec, 5)


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


DRAWS = [(1, "Bs", "Jh8h3c", "2s", "Ah5h"), (2, "X", "Jh8h3c", "2s", "Ts9s"),  # Flush draw nuts, OESD
         (3, "X", "Jh8h3c", "2s", "AsKd"), (4, "Bs", "Jh8h3c", "2s", "AcKc")]  # No draw, BDFD 2 cards


def draws_by_id(hands):
    return dict(zip(hands["id_hand"], hands["draw_type"]))


def test_draw_type_on_flop_decision(monkeypatch):
    install(monkeypatch, fake_matches(DRAWS))
    hands = spotlight.run_spot("2bp", "ip", "pfr", "- ?")["hands"]
    assert draws_by_id(hands) == {1: "Flush draw nuts", 2: "OESD", 3: "No draw", 4: "BDFD 2 cards"}


def test_draw_type_on_turn_decision(monkeypatch):
    install(monkeypatch, fake_matches(DRAWS))
    hands = spotlight.run_spot("2bp", "ip", "pfr", "- B-?")["hands"]
    assert draws_by_id(hands) == {1: "Combo draw", 2: "OESD", 3: "No draw", 4: "No draw"}


def test_draw_type_on_river_decision(monkeypatch):
    install(monkeypatch, fake_matches([(1, "B", "Jh8h3c", "2s5d", "AhKh")]))
    hands = spotlight.run_spot("2bp", "ip", "pfr", "- B-B-?")["hands"]
    assert draws_by_id(hands) == {1: "No draw"}


def test_draw_filter_or_within(monkeypatch):
    install(monkeypatch, fake_matches(DRAWS))
    hands = spotlight.run_spot("2bp", "ip", "pfr", "- ?", draw_types=["OESD", "BDFD 2 cards"])["hands"]
    assert set(hands["id_hand"]) == {2, 4}


def test_draw_and_hand_type(monkeypatch):
    install(monkeypatch, fake_matches(DRAWS))
    hands = spotlight.run_spot("2bp", "ip", "pfr", "- ?", hand_types=["Ace high"], draw_types=["No draw"])["hands"]
    assert set(hands["id_hand"]) == {3}


def test_draw_filter_on_river_is_allowed(monkeypatch):
    install(monkeypatch, fake_matches([(1, "B", "Jh8h3c", "2s5d", "AhKh")]))
    hands = spotlight.run_spot("2bp", "ip", "pfr", "- B-B-?", draw_types=["No draw"])["hands"]
    assert list(hands["id_hand"]) == [1]


def test_unknown_draw_type_raises(monkeypatch):
    monkeypatch.setattr("spotlight.run_spot_query", no_query)
    with pytest.raises(SpotInputError, match="Unknown draw type: Monster"):
        spotlight.run_spot("2bp", "ip", "pfr", "- ?", draw_types=["Monster"])


def test_describe_draw_part(monkeypatch):
    install(monkeypatch, fake_matches(DRAWS))
    text = spotlight.run_spot("2bp", "ip", "pfr", "- ?", hand_types=["Ace high"],
                              draw_types=["OESD", "No draw", "OESD"])["interpreted_filter"]
    assert "· Hand: Ace high · Draw: OESD, No draw · Flop: " in text
    assert "Draw:" not in spotlight.run_spot("2bp", "ip", "pfr", "- ?")["interpreted_filter"]


def test_draw_split_rows_cells_and_pcts(monkeypatch):
    install(monkeypatch, fake_matches(DRAWS))
    split = spotlight.run_spot("2bp", "ip", "pfr", "- ?")["draw_split"]
    assert [(r["draw_type"], r["hands"], r["pct_total"]) for r in split] == [
        ("Flush draw nuts", 1, 25.0), ("OESD", 1, 25.0), ("BDFD 2 cards", 1, 25.0), ("No draw", 1, 25.0)]
    assert [(c["label"], c["hands"], c["pct"]) for c in split[0]["cells"]] == [
        ("B", 1, 100.0), ("Bs", 1, 100.0), ("Bm", 0, 0.0), ("Bl", 0, 0.0), ("Bo", 0, 0.0), ("X", 0, 0.0)]


def test_draw_split_empty_list_when_no_hands(monkeypatch):
    install(monkeypatch, fake_matches(DRAWS))
    assert spotlight.run_spot("2bp", "ip", "pfr", "- ?", draw_types=["Gutshot"])["draw_split"] == []
