import pytest
import pandas as pd
from query_router import run_query

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