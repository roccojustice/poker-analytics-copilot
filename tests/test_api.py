from datetime import date
from fastapi.testclient import TestClient
from api import app
import pandas as pd
from line_parser import SpotInputError

client = TestClient(app)

def test_query_golden_path(monkeypatch):
    fake_parsed = {"query_name": "winrate", "group_by": "position"}
    fake_df = pd.DataFrame({'pos': ['BB'], 'amt_won': [1], 'amt_bb': [1]})
    fake_df = fake_df.set_index('pos')

    def fake_parse_user_query(question):
        return fake_parsed

    def fake_run_query(query_name, group_by=None, limit=None):
        return fake_df

    monkeypatch.setattr("api.parse_user_query", fake_parse_user_query)
    monkeypatch.setattr("api.run_query", fake_run_query)

    response = client.post("/query", json={"question": "winrate by position"})

    assert response.status_code == 200
    assert response.json() == {"result": [{"pos": "BB", "amt_won": 1, "amt_bb": 1}]}

def test_query_endpoint_returns_distribution_shape_for_line_query(monkeypatch):
    fake_parsed = {"query_name": "2bp_ip_pfr_turn_cbet_opp"}
    fake_result = {
        "interpreted_filter": "2bp_ip_pfr_turn_cbet_opp",
        "distribution": {"check": {"count": 60, "pct": 60.0}, "bet": {"count": 40, "pct": 40.0}},
        "hands": pd.DataFrame({"id_hand": [1, 2, 3], "cards": ["AhKh", "2c3d", "9s9h"]}),
    }

    monkeypatch.setattr("api.parse_user_query", lambda question: fake_parsed)
    monkeypatch.setattr("api.run_query", lambda query_name, limit=None: fake_result)

    response = client.post("/query", json={"question": "frecuencias de bet en 2bp ip pfr turno"})

    assert response.status_code == 200
    assert response.json() == {
        "result": {
            "interpreted_filter": "2bp_ip_pfr_turn_cbet_opp",
            "distribution": {"check": {"count": 60, "pct": 60.0}, "bet": {"count": 40, "pct": 40.0}},
            "hands": [
                {"id_hand": 1, "cards": "AhKh"},
                {"id_hand": 2, "cards": "2c3d"},
                {"id_hand": 3, "cards": "9s9h"},
            ],
        }
    }, "distribution-backed queries must serialize the hands DataFrame, passing distribution/interpreted_filter through as-is"

def test_query_endpoint_returns_clarifying_question(monkeypatch):
    fake_parsed = {
        "query_name": "ask_clarifying_question",
        "question": "Do you mean 2bp or 3bp?",
    }

    monkeypatch.setattr("api.parse_user_query", lambda question: fake_parsed)

    response = client.post("/query", json={"question": "frecuencias de bet, bb opp"})

    assert response.status_code == 200
    assert response.json() == {"clarifying_question": "Do you mean 2bp or 3bp?"}

def test_handle_unexpected_exception(monkeypatch):
    client_no_raise = TestClient(app, raise_server_exceptions=False)

    def fake_parse_user_query(question):
        raise Exception("Test exception")

    monkeypatch.setattr("api.parse_user_query", fake_parse_user_query)

    response = client_no_raise.post("/query", json={"question": "winrate by position"})

    assert response.status_code == 500
    assert response.json() == {"error": "Something went wrong processing your question. Please try again."}


SPOT_BODY = {"pot": "2bp", "position": "ip", "role": "pfr", "line": "XC-X", "formations": []}


def install_fake_run_spot(monkeypatch, result):
    calls = []

    def fake_run_spot(pot, position, role, line, formations=(), date_from=None, date_to=None, flop_types=(), turn_types=(), river_types=(), hand_types=(), draw_types=()):
        calls.append((pot, position, role, line, formations))
        return result

    monkeypatch.setattr("api.run_spot", fake_run_spot)
    return calls


FAKE_RESULT = {
    "interpreted_filter": "2BP · IP · PFR · Any · ...",
    "distribution": [{"action": "B", "label": "B", "name": "Bet", "hands": 1, "pct": 100.0}],
    "hands": pd.DataFrame({"id_hand": [1], "measured_action": ["B"]}),
    "split": None,
    "hand_split": [],
    "draw_split": [],
}


def test_spot_returns_result_shape(monkeypatch):
    calls = install_fake_run_spot(monkeypatch, FAKE_RESULT)
    response = client.post("/spot", json=SPOT_BODY)
    assert response.status_code == 200
    assert response.json() == {
        "interpreted_filter": "2BP · IP · PFR · Any · ...",
        "distribution": [{"action": "B", "label": "B", "name": "Bet", "hands": 1, "pct": 100.0}],
        "hands": [{"id_hand": 1, "measured_action": "B"}],
        "split": None,
        "hand_split": [],
        "draw_split": [],
    }
    assert calls == [("2bp", "ip", "pfr", "XC-X", [])]


def test_spot_passes_split_through(monkeypatch):
    split = [{"size": "S", "name": "small", "hands": 1, "pct_faced": 100.0,
              "cells": [{"action": "C", "label": "XCs", "hands": 1, "pct": 100.0}]}]
    install_fake_run_spot(monkeypatch, FAKE_RESULT | {"split": split})
    assert client.post("/spot", json=SPOT_BODY).json()["split"] == split


def test_spot_passes_formations_through(monkeypatch):
    calls = install_fake_run_spot(monkeypatch, FAKE_RESULT)
    client.post("/spot", json=SPOT_BODY | {"formations": ["BB vs BTN", "BB vs CO"]})
    assert calls[0][4] == ["BB vs BTN", "BB vs CO"]


def test_spot_formations_default_to_empty(monkeypatch):
    calls = install_fake_run_spot(monkeypatch, FAKE_RESULT)
    body = {k: v for k, v in SPOT_BODY.items() if k != "formations"}
    client.post("/spot", json=body)
    assert calls[0][4] == []


def test_spot_input_error_is_400_with_message(monkeypatch):
    def fake_run_spot(*args, **kwargs):
        raise SpotInputError("Unknown formation: BTN vs BB")

    monkeypatch.setattr("api.run_spot", fake_run_spot)
    response = client.post("/spot", json=SPOT_BODY | {"formations": ["BTN vs BB"]})
    assert response.status_code == 400
    assert response.json() == {"error": "Unknown formation: BTN vs BB"}


def test_spot_old_grammar_is_400():
    response = client.post("/spot", json=SPOT_BODY | {"line": "- B-"})
    assert response.status_code == 400
    assert response.json() == {"error": "A Line is the villain's actions: no leading '-'"}


def test_spot_real_parser_error_is_400():
    response = client.post("/spot", json=SPOT_BODY | {"line": "XC"})
    assert response.status_code == 400
    assert "villain acts next" in response.json()["error"]


def test_spot_rejects_the_old_formation_field(monkeypatch):
    install_fake_run_spot(monkeypatch, FAKE_RESULT)
    response = client.post("/spot", json=SPOT_BODY | {"formation": "BB vs BTN"})
    assert response.status_code == 422


def test_spot_passes_dates_through(monkeypatch):
    seen = {}

    def fake_run_spot(pot, position, role, line, formations=(), date_from=None, date_to=None, flop_types=(), turn_types=(), river_types=(), hand_types=(), draw_types=()):
        seen.update(date_from=date_from, date_to=date_to)
        return FAKE_RESULT

    monkeypatch.setattr("api.run_spot", fake_run_spot)
    client.post("/spot", json=SPOT_BODY | {"date_from": "2026-09-01", "date_to": "2026-10-15"})
    assert seen == {"date_from": date(2026, 9, 1), "date_to": date(2026, 10, 15)}


def test_spot_dates_default_to_none(monkeypatch):
    seen = {}

    def fake_run_spot(pot, position, role, line, formations=(), date_from="unset", date_to="unset", flop_types=(), turn_types=(), river_types=(), hand_types=(), draw_types=()):
        seen.update(date_from=date_from, date_to=date_to)
        return FAKE_RESULT

    monkeypatch.setattr("api.run_spot", fake_run_spot)
    client.post("/spot", json=SPOT_BODY)
    assert seen == {"date_from": None, "date_to": None}


def test_spot_inverted_dates_is_400():
    response = client.post("/spot", json=SPOT_BODY | {"date_from": "2026-10-02", "date_to": "2026-10-01"})
    assert response.status_code == 400
    assert response.json() == {"error": "From date is after To date"}


def test_spot_malformed_date_is_422():
    response = client.post("/spot", json=SPOT_BODY | {"date_from": "2026-13-45"})
    assert response.status_code == 422


def test_spot_passes_flop_types_through(monkeypatch):
    seen = {}

    def fake_run_spot(pot, position, role, line, formations=(), date_from=None, date_to=None, flop_types="unset", turn_types=(), river_types=(), hand_types=(), draw_types=()):
        seen["flop_types"] = flop_types
        return FAKE_RESULT

    monkeypatch.setattr("api.run_spot", fake_run_spot)
    client.post("/spot", json=SPOT_BODY | {"flop_types": ["BLL", "Low"]})
    assert seen == {"flop_types": ["BLL", "Low"]}


def test_spot_flop_types_default_to_empty(monkeypatch):
    seen = {}

    def fake_run_spot(pot, position, role, line, formations=(), date_from=None, date_to=None, flop_types="unset", turn_types=(), river_types=(), hand_types=(), draw_types=()):
        seen["flop_types"] = flop_types
        return FAKE_RESULT

    monkeypatch.setattr("api.run_spot", fake_run_spot)
    client.post("/spot", json=SPOT_BODY)
    assert seen == {"flop_types": []}


def test_spot_unknown_flop_type_is_400():
    response = client.post("/spot", json=SPOT_BODY | {"flop_types": ["bll"]})
    assert response.status_code == 400
    assert "bll" in response.json()["error"]


def test_spot_passes_runout_types_through(monkeypatch):
    seen = {}

    def fake_run_spot(*args, turn_types="unset", river_types="unset", **kwargs):
        seen.update(turn_types=turn_types, river_types=river_types)
        return FAKE_RESULT

    monkeypatch.setattr("api.run_spot", fake_run_spot)
    client.post("/spot", json=SPOT_BODY | {"turn_types": ["FC", "SC"], "river_types": ["Brick"]})
    assert seen == {"turn_types": ["FC", "SC"], "river_types": ["Brick"]}


def test_spot_runout_types_default_to_empty(monkeypatch):
    seen = {}

    def fake_run_spot(*args, turn_types="unset", river_types="unset", **kwargs):
        seen.update(turn_types=turn_types, river_types=river_types)
        return FAKE_RESULT

    monkeypatch.setattr("api.run_spot", fake_run_spot)
    client.post("/spot", json=SPOT_BODY)
    assert seen == {"turn_types": [], "river_types": []}


def test_spot_unknown_turn_type_is_400():
    response = client.post("/spot", json=SPOT_BODY | {"line": "XC-X", "turn_types": ["fc"]})
    assert response.status_code == 400
    assert "fc" in response.json()["error"]


def test_spot_river_types_on_turn_line_is_400():
    response = client.post("/spot", json=SPOT_BODY | {"line": "XC-X", "river_types": ["Brick"]})
    assert response.status_code == 400
    assert "river" in response.json()["error"]


def test_spot_passes_hand_split_through(monkeypatch):
    hand_split = [{"hand_type": "Top pair", "hands": 1, "pct_total": 100.0,
                   "cells": [{"action": "X", "label": "X", "name": "Check", "hands": 1, "pct": 100.0}]}]
    install_fake_run_spot(monkeypatch, FAKE_RESULT | {"hand_split": hand_split})
    assert client.post("/spot", json=SPOT_BODY).json()["hand_split"] == hand_split


def test_spot_passes_hand_types_through(monkeypatch):
    seen = []

    def fake_run_spot(*args, hand_types="unset", **kwargs):
        seen.append(hand_types)
        return FAKE_RESULT

    monkeypatch.setattr("api.run_spot", fake_run_spot)
    client.post("/spot", json=SPOT_BODY | {"hand_types": ["Top pair"]})
    client.post("/spot", json=SPOT_BODY)
    assert seen == [["Top pair"], []]


def test_spot_unknown_hand_type_is_400():
    response = client.post("/spot", json=SPOT_BODY | {"hand_types": ["Monster"]})
    assert response.status_code == 400
    assert response.json() == {"error": "Unknown hand type: Monster"}


def test_spot_passes_draw_split_through(monkeypatch):
    draw_split = [{"draw_type": "OESD", "hands": 1, "pct_total": 100.0,
                   "cells": [{"action": "X", "label": "X", "name": "Check", "hands": 1, "pct": 100.0}]}]
    install_fake_run_spot(monkeypatch, FAKE_RESULT | {"draw_split": draw_split})
    assert client.post("/spot", json=SPOT_BODY).json()["draw_split"] == draw_split


def test_spot_passes_draw_types_through(monkeypatch):
    seen = []

    def fake_run_spot(*args, draw_types="unset", **kwargs):
        seen.append(draw_types)
        return FAKE_RESULT

    monkeypatch.setattr("api.run_spot", fake_run_spot)
    client.post("/spot", json=SPOT_BODY | {"draw_types": ["OESD"]})
    client.post("/spot", json=SPOT_BODY)
    assert seen == [["OESD"], []]


def test_spot_unknown_draw_type_is_400():
    response = client.post("/spot", json=SPOT_BODY | {"draw_types": ["Monster"]})
    assert response.status_code == 400
    assert response.json() == {"error": "Unknown draw type: Monster"}
