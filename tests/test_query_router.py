import pytest
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