from fastapi.testclient import TestClient
from api import app
import pandas as pd

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
