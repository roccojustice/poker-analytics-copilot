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

def test_handle_unexpected_exception(monkeypatch):
    client_no_raise = TestClient(app, raise_server_exceptions=False)

    def fake_parse_user_query(question):
        raise Exception("Test exception")

    monkeypatch.setattr("api.parse_user_query", fake_parse_user_query)

    response = client_no_raise.post("/query", json={"question": "winrate by position"})

    assert response.status_code == 500
    assert response.json() == {"error": "Something went wrong processing your question. Please try again."}