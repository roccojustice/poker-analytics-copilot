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

def test_run_filter_query_with_since_date(monkeypatch):
    monkeypatch.setattr("db.pd.read_sql", fake_read_sql)
    result = run_filter_query("check_river_2bp_ip_pfr", id_player=42, since_date="2023-01-01")
    assert "AND chps.date_played >= %(since_date)s" in result["query"]
    assert result["params"] == {"id_player": 42, "since_date": "2023-01-01"}

def test_run_filter_query_without_since_date_does_not_filter(monkeypatch):
    monkeypatch.setattr("db.pd.read_sql", fake_read_sql)
    result = run_filter_query("check_river_2bp_ip_pfr", id_player=42)
    assert "date_played" not in result["query"]
    assert "since_date" not in result["params"]

def test_run_filter_query_clause_order_with_since_date_and_limit(monkeypatch):
    monkeypatch.setattr("db.pd.read_sql", fake_read_sql)
    result = run_filter_query("check_river_2bp_ip_pfr", id_player=42, since_date="2023-01-01", limit=10)
    query = result["query"]
    since_date_pos = query.index("chps.date_played >= %(since_date)s")
    order_by_pos = query.index("ORDER BY")
    limit_pos = query.index("LIMIT")
    assert since_date_pos < order_by_pos < limit_pos, "SQL clauses must appear in order: WHERE conditions, then ORDER BY, then LIMIT"
    assert result["params"] == {"id_player": 42, "since_date": "2023-01-01", "limit": 10}