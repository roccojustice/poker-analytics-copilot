from datetime import date
import pandas as pd
import pytest
from analytics import compute_distribution
from db import run_filter_query, run_spot_query
from filter_recipes import build_where_clause
from line_parser import parse_line
from lines import LINES
from spot_sql import build_spot_query
from spotlight import run_spot

pytestmark = pytest.mark.db

ORACLE = [
    ("2bp_ip_pfr_turn_cbet_opp", "2bp", "ip", "pfr", "XC-X"),
    ("2bp_oop_pfr_turn_cbet_opp", "2bp", "oop", "pfr", "C"),
    ("3bp_ip_pfr_turn_cbet_opp", "3bp", "ip", "pfr", "XC-X"),
    ("3bp_oop_pfr_turn_cbet_opp", "3bp", "oop", "pfr", "C"),
    ("2bp_ip_pfc_faced_cbet_flop", "2bp", "ip", "pfc", "B"),
    ("2bp_oop_pfc_faced_cbet_flop", "2bp", "oop", "pfc", "B"),
    ("3bp_ip_pfc_faced_cbet_flop", "3bp", "ip", "pfc", "B"),
    ("3bp_oop_pfc_faced_cbet_flop", "3bp", "oop", "pfc", "B"),
    ("3bp_ip_pfc_faced_barrel_turn", "3bp", "ip", "pfc", "B-B"),
]
NAME_TO_LETTER = {"bet": "B", "check": "X", "raise": "R", "call": "C", "fold": "F"}
JUSTIFIED_EXCEPTIONS = {}  # recipe -> {"extra": set(), "missing": set()}, each documented in SCHEMA_NOTES.md


@pytest.mark.parametrize("recipe, pot, position, role, line", ORACLE)
def test_spotlight_matches_recipe(recipe, pot, position, role, line):
    where, params = build_where_clause(recipe)
    recipe_hands = set(run_filter_query(where, params)["id_hand"])

    spec = parse_line(line, role, position)
    s_where, s_params, measured_sql = build_spot_query(pot, position, role, spec)
    spot = run_spot_query(s_where, s_params, measured_sql)
    spot_hands = set(spot["id_hand"])

    allowed = JUSTIFIED_EXCEPTIONS.get(recipe, {"extra": set(), "missing": set()})
    extra = spot_hands - recipe_hands - allowed["extra"]
    missing = recipe_hands - spot_hands - allowed["missing"]
    assert not extra and not missing, (
        f"{recipe}: {len(extra)} extra {sorted(extra)[:10]}, {len(missing)} missing {sorted(missing)[:10]}"
    )

    if not allowed["extra"] and not allowed["missing"]:
        recipe_dist = compute_distribution(where, params, LINES[recipe])
        expected = {NAME_TO_LETTER[name]: v["count"] for name, v in recipe_dist.items() if v["count"]}
        assert spot["measured_action"].str[0].value_counts().to_dict() == expected


def test_formations_pool_as_union_of_single_formations():
    spec = parse_line("B", "pfc", "oop")

    def hands(formations):
        where, params, measured_sql = build_spot_query("2bp", "oop", "pfc", spec, formations)
        return set(run_spot_query(where, params, measured_sql)["id_hand"])

    btn, co = hands(["BB vs BTN"]), hands(["BB vs CO"])
    assert btn and co and not (btn & co)
    assert hands(["BB vs BTN", "BB vs CO"]) == btn | co


def test_date_range_matches_filtering_the_full_result_by_day():
    date_from, date_to = date(2026, 7, 1), date(2026, 8, 5)
    full = run_spot("2bp", "oop", "pfc", "B")["hands"]
    days = pd.to_datetime(full["date_played"]).dt.date
    expected = set(full.loc[(days >= date_from) & (days <= date_to), "id_hand"])

    ranged = run_spot("2bp", "oop", "pfc", "B", [], date_from, date_to)

    assert set(ranged["hands"]["id_hand"]) == expected
    assert sum(row["hands"] for row in ranged["distribution"]) == len(expected)
    assert (days == date_to).any()  # the To day itself has hands, so inclusivity is tested
