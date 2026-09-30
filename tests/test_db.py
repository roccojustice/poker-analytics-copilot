import pandas as pd
import pytest
from db import (
    run_filter_query,
    run_distribution_query,
    get_hand_details,
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

def test_get_hand_details_orders_newest_first(monkeypatch):
    captured = {}

    def fake_read_sql(query, engine, params=None):
        captured["query"] = query
        return pd.DataFrame([{
            "id_hand": 1,
            "date_played": "2025-01-01",
            "position": "BTN",
            "final_hand_group": "One Pair",
            "final_hand_details": "Aces",
            "holecard_1": 1,
            "holecard_2": 2,
            "card_1": 0,
            "card_2": 0,
            "card_3": 0,
            "card_4": 0,
            "card_5": 0,
            "f_act": "B",
            "t_act": "X",
            "r_act": "F",
            "amt_bet_f": 0.32,
            "amt_bet_t": 0,
            "amt_bet_r": 0,
            "amt_pot": 1.98,
            "amt_bb": 0.25,
            "amt_won": -0.94,
            "winner": "villain",
            "winning_hand_group": "One Pair",
            "winning_hand_details": "Kings",
        }])

    monkeypatch.setattr("db.pd.read_sql", fake_read_sql)
    get_hand_details([1])

    assert "ORDER BY chps.date_played DESC" in captured["query"], (
        "hand list must show the most recently played hands first"
    )

def test_run_distribution_query_builds_count_filter_per_action(monkeypatch):
    monkeypatch.setattr("db.pd.read_sql", fake_read_sql)
    conditions = [("check", "chps.flg_t_check = true"), ("bet", "chps.flg_t_check = false")]
    result = run_distribution_query(
        " AND flg_x = true", {}, conditions, id_player=42
    )
    query = result["query"]
    assert "COUNT(*) FILTER (WHERE chps.flg_t_check = true) AS check" in query, (
        "one COUNT(*) FILTER column per action, named after the action"
    )
    assert "COUNT(*) FILTER (WHERE chps.flg_t_check = false) AS bet" in query
    assert " AND flg_x = true" in query, "the recipe's where_clause must still gate the filtered hand set"
    assert result["params"] == {"id_player": 42}, (
        "condition SQL is a trusted static fragment (like ATOMIC_FILTERS), not a bound value"
    )

def test_run_distribution_query_supports_more_than_two_actions(monkeypatch):
    monkeypatch.setattr("db.pd.read_sql", fake_read_sql)
    conditions = [
        ("raise", "chps.cnt_f_raise >= 1"),
        ("fold", "chps.cnt_f_raise = 0 AND chps.flg_f_fold = true"),
        ("call", "chps.cnt_f_raise = 0 AND chps.flg_f_fold = false"),
    ]
    result = run_distribution_query(" AND flg_x = true", {}, conditions, id_player=42)
    query = result["query"]
    assert "COUNT(*) FILTER (WHERE chps.cnt_f_raise >= 1) AS raise" in query
    assert "COUNT(*) FILTER (WHERE chps.cnt_f_raise = 0 AND chps.flg_f_fold = true) AS fold" in query
    assert "COUNT(*) FILTER (WHERE chps.cnt_f_raise = 0 AND chps.flg_f_fold = false) AS call" in query
