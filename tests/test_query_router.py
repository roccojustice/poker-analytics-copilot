import pytest
import pandas as pd
from query_router import run_query
from filter_recipes import build_where_clause, assemble_where

def test_run_query_with_limit():
    with pytest.raises(ValueError):
        run_query("winrate", group_by="pos", limit=10)

def test_run_query_with_group_by():
    with pytest.raises(ValueError):
        run_query("check_river_2bp_ip_pfr", group_by="pos", limit=None)

def test_run_query_with_unknown_query():
    with pytest.raises(ValueError):
        run_query("unknown_query", group_by=None, limit=None)

def test_run_query_with_invalid_group_by():
    with pytest.raises(ValueError):
        run_query("winrate", group_by="invalid_group", limit=None)

def test_run_query_with_none_group_by_for_metric():
    with pytest.raises(ValueError):
        run_query("winrate", group_by=None, limit=None)

def test_run_query_with_since_date(monkeypatch):
    fake_df = pd.DataFrame({
        'position': ['BB', 'BB', 'BB'],
        'amt_won': [10, -20, 30],
        'amt_bb': [1, 1, 1],
        'date_played': pd.to_datetime(['2023-01-01', '2023-02-01', '2023-03-01']),
    })

    def fake_get_hero_df():
        return fake_df

    monkeypatch.setattr("query_router.get_hero_df", fake_get_hero_df)

    result = run_query("winrate", group_by="position", since_date="2023-02-01")

    assert result.loc["BB", "hands"] == 2, "Only hands from 2023-02-01 onward should count"
    assert result.loc["BB", "bb_per_100"] == 500, "bb_per_100 should reflect only the filtered hands"

def test_run_query_filter_branch_builds_where_from_recipe_name(monkeypatch):
    captured = {}

    def fake_run_filter_query(where_clause, params, limit=None, since_date=None):
        captured["where_clause"] = where_clause
        captured["params"] = params
        return pd.DataFrame({"id_hand": [1, 2, 3]})

    monkeypatch.setattr("query_router.run_filter_query", fake_run_filter_query)
    monkeypatch.setattr("query_router.get_hand_details", lambda id_hands: list(id_hands))

    result = run_query("check_river_2bp_ip_pfr")

    expected_where, expected_params = build_where_clause("check_river_2bp_ip_pfr")
    assert captured["where_clause"] == expected_where, "with no active_filters, the WHERE must come from build_where_clause(query_name)"
    assert captured["params"] == expected_params
    assert result == [1, 2, 3], "the id_hand series must be threaded through to get_hand_details"

def test_run_query_filter_branch_uses_active_filters_when_given(monkeypatch):
    captured = {}

    def fake_run_filter_query(where_clause, params, limit=None, since_date=None):
        captured["where_clause"] = where_clause
        captured["params"] = params
        return pd.DataFrame({"id_hand": [7]})

    monkeypatch.setattr("query_router.run_filter_query", fake_run_filter_query)
    monkeypatch.setattr("query_router.get_hand_details", lambda id_hands: list(id_hands))

    active = ["first_raise", ("total_raises", ">=", 2)]
    run_query("check_river_2bp_ip_pfr", active_filters=active)

    expected_where, expected_params = assemble_where(active)
    assert captured["where_clause"] == expected_where, "active_filters must be assembled, not the recipe named by query_name"
    assert captured["params"] == expected_params

    recipe_where, _ = build_where_clause("check_river_2bp_ip_pfr")
    assert captured["where_clause"] != recipe_where, "the recipe's own WHERE must be ignored when active_filters is passed"
