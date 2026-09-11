import pytest
from db import (
    run_filter_query,
    run_distribution_query,
)

def fake_read_sql(query, engine, params=None):
    captured = {}
    captured["query"] = query
    captured["params"] = params
    return captured

def test_run_filter_query(monkeypatch):
    monkeypatch.setattr("db.pd.read_sql", fake_read_sql)
    result = run_filter_query(" AND hrt.total_p_raises = %(tr)s", {"tr": 1}, id_player=42, limit=10)
    assert " AND hrt.total_p_raises = %(tr)s" in result["query"]
    assert result["params"] == {"tr": 1, "id_player": 42, "limit": 10}

def test_run_filter_query_with_since_date(monkeypatch):
    monkeypatch.setattr("db.pd.read_sql", fake_read_sql)
    result = run_filter_query(" AND flg_x = true", {}, id_player=42, since_date="2023-01-01")
    assert "AND chps.date_played >= %(since_date)s" in result["query"]
    assert result["params"] == {"id_player": 42, "since_date": "2023-01-01"}

def test_run_filter_query_without_since_date_does_not_filter(monkeypatch):
    monkeypatch.setattr("db.pd.read_sql", fake_read_sql)
    result = run_filter_query(" AND flg_x = true", {}, id_player=42)
    assert "date_played" not in result["query"]
    assert "since_date" not in result["params"]

def test_run_filter_query_clause_order_with_since_date_and_limit(monkeypatch):
    monkeypatch.setattr("db.pd.read_sql", fake_read_sql)
    result = run_filter_query(" AND flg_x = true", {}, id_player=42, since_date="2023-01-01", limit=10)
    query = result["query"]
    since_date_pos = query.index("chps.date_played >= %(since_date)s")
    order_by_pos = query.index("ORDER BY")
    limit_pos = query.index("LIMIT")
    assert since_date_pos < order_by_pos < limit_pos, "SQL clauses must appear in order: WHERE conditions, then ORDER BY, then LIMIT"
    assert result["params"] == {"id_player": 42, "since_date": "2023-01-01", "limit": 10}

def test_run_distribution_query_builds_count_filter_per_action(monkeypatch):
    monkeypatch.setattr("db.pd.read_sql", fake_read_sql)
    result = run_distribution_query(
        " AND flg_x = true", {}, "flg_t_check", {True: "check", False: "bet"}, id_player=42
    )
    query = result["query"]
    assert "COUNT(*) FILTER (WHERE chps.flg_t_check = %(is_check)s) AS check" in query, (
        "one COUNT(*) FILTER column per action, named after the action"
    )
    assert "COUNT(*) FILTER (WHERE chps.flg_t_check = %(is_bet)s) AS bet" in query
    assert " AND flg_x = true" in query, "the recipe's where_clause must still gate the filtered hand set"
    assert result["params"] == {"is_check": True, "is_bet": False, "id_player": 42}, (
        "each action's boolean value must be bound, not interpolated into the query string"
    )
