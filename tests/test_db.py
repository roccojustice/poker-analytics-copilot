import pandas as pd
import pytest
from db import (
    run_filter_query,
    run_distribution_query,
    get_hand_details,
    run_spot_query,
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

HAND_ROW = {
    "id_hand": 1,
    "hand_no": "261654385495",
    "date_played": "2025-01-01",
    "position": "BTN",
    "limit_name": "$0.02 NL (6 max)",
    "final_hand_group": "One Pair",
    "final_hand_details": "Aces",
    "holecard_1": 1,
    "holecard_2": 2,
    "card_1": 0,
    "card_2": 0,
    "card_3": 0,
    "card_4": 0,
    "card_5": 0,
    "f_act": "XC",
    "t_act": "B",
    "r_act": "X",
    "amt_bet_f": 0.06,
    "amt_bet_t": 0.10,
    "amt_bet_r": 0,
    "amt_pot_f": 0.13,
    "amt_pot_t": 0.25,
    "amt_pot_r": 0.45,
    "amt_f_bet_made": 0,
    "amt_f_bet_facing": 0.06,
    "amt_t_bet_made": 0.10,
    "amt_t_bet_facing": 0,
    "amt_r_bet_made": 0,
    "amt_r_bet_facing": 0,
    "amt_pot": 0.53,
    "amt_bb": 0.02,
    "amt_won": -0.20,
    "winner": "villain",
    "winning_hand_group": "One Pair",
    "winning_hand_details": "Kings",
}

def test_get_hand_details_orders_newest_first(monkeypatch):
    captured = {}

    def fake_read_sql(query, engine, params=None):
        captured["query"] = query
        return pd.DataFrame([HAND_ROW])

    monkeypatch.setattr("db.pd.read_sql", fake_read_sql)
    get_hand_details([1])

    assert "ORDER BY chps.date_played DESC" in captured["query"], (
        "hand list must show the most recently played hands first"
    )

def test_get_hand_details_adds_stake_and_amounts_in_bb(monkeypatch):
    monkeypatch.setattr("db.pd.read_sql", lambda query, engine, params=None: pd.DataFrame([HAND_ROW]))

    row = get_hand_details([1]).iloc[0]

    assert row.get("stake") == "$0.02 NL (6 max)"
    assert row.get("pot_bb") == pytest.approx(26.5)
    assert row.get("result_bb") == pytest.approx(-10.0)

@pytest.mark.parametrize("amt_won, amt_bb, expected", [(0.30, 0.10, 3.0), (-0.30, 0.10, -3.0), (-0.60, 0.10, -6.0)])
def test_get_hand_details_result_bb_is_exact_at_whole_bb(monkeypatch, amt_won, amt_bb, expected):
    row = {**HAND_ROW, "amt_won": amt_won, "amt_bb": amt_bb}
    monkeypatch.setattr("db.pd.read_sql", lambda query, engine, params=None: pd.DataFrame([row]))

    assert get_hand_details([1]).iloc[0]["result_bb"] == expected  # no approx: the page filters with >= / <=

def test_get_hand_details_bet_size_is_pct_of_pot_at_street_start(monkeypatch):
    monkeypatch.setattr("db.pd.read_sql", lambda query, engine, params=None: pd.DataFrame([HAND_ROW]))

    row = get_hand_details([1]).iloc[0]

    assert row.get("f_size") == pytest.approx(100 * 0.06 / 0.13)  # faced, not PT4's bet/(pot+bet)
    assert row.get("t_size") == pytest.approx(100 * 0.10 / 0.25)  # made
    assert pd.isna(row.get("r_size", 0))                           # no bet on the river

@pytest.mark.db
@pytest.mark.parametrize("hand_no, expected", [
    ("261654386261", "UTG"),    # code 3, 6-handed
    ("261654433397", "MP"),     # code 2, 6-handed
    ("257721989956", "MP+1"),   # code 3, 9-handed
])
def test_get_hand_details_position_name_depends_on_table_size(hand_no, expected):
    from db import engine
    id_hand = pd.read_sql(
        "SELECT id_hand FROM cash_hand_summary WHERE hand_no = %(h)s", engine, params={"h": hand_no}
    )["id_hand"].item()

    df = get_hand_details([id_hand])

    assert df["position"].tolist() == [expected]

@pytest.mark.db
def test_get_hand_details_real_hand_sizes_and_stake():
    from db import engine
    id_hand = pd.read_sql(
        "SELECT id_hand FROM cash_hand_summary WHERE hand_no = '261654385495'", engine
    )["id_hand"].item()

    row = get_hand_details([id_hand]).iloc[0]

    assert row["stake"] == "$0.02 NL (6 max)"
    assert row["f_size"] == pytest.approx(100 * 0.06 / 0.13)  # XC vs 0.06 into 0.13
    assert row["t_size"] == pytest.approx(100 * 0.14 / 0.25)  # faced 0.14 into 0.25

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


def test_run_spot_query_builds_skeleton_and_binds_params(monkeypatch):
    monkeypatch.setattr("db.pd.read_sql", fake_read_sql)
    result = run_spot_query(" AND h_f.action = %(h_f)s", {"h_f": "B"},
                            "substr(h_t.action, %(measure_pos)s, 1)", id_player=42)
    query = result["query"]
    assert "substr(h_t.action, %(measure_pos)s, 1) AS measured_action" in query
    assert "chs.card_1, chs.card_2, chs.card_3, chs.card_4, chs.card_5" in query
    assert "chps.holecard_1, chps.holecard_2" in query
    assert "v.id_player <> chps.id_player AND v.flg_f_saw = true" in query
    for alias in ("h_f", "h_t", "h_r", "v_f", "v_t", "v_r"):
        assert f"lookup_actions {alias} ON" in query
    assert query.rstrip().endswith("ORDER BY chps.id_hand")
    assert " AND h_f.action = %(h_f)s" in query
    assert result["params"] == {"h_f": "B", "id_player": 42}
