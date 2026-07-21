import pytest
from db import (
    run_filter_query,
    FILTER_QUERIES
)

def fake_read_sql(query, engine, params=None):
    captured = {}
    captured["query"] = query
    captured["params"] = params
    return captured

def test_run_filter_query_wrong_name():
    with pytest.raises(ValueError):
        run_filter_query("winrate", id_player=42, limit=10)

def test_run_filter_query(monkeypatch):
    monkeypatch.setattr("db.pd.read_sql", fake_read_sql)
    result = run_filter_query("check_river_2bp_ip_pfr", id_player=42, limit=10)
    assert FILTER_QUERIES["check_river_2bp_ip_pfr"] in result["query"] 
    assert result["params"] == {"id_player": 42, "limit": 10}