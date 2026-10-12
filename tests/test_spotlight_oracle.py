import pytest
from analytics import compute_distribution
from db import run_filter_query, run_spot_query
from filter_recipes import build_where_clause
from line_parser import parse_line
from lines import LINES
from spot_sql import build_spot_query

pytestmark = pytest.mark.db

ORACLE = [
    ("2bp_ip_pfr_turn_cbet_opp", "2bp", "ip", "pfr", "- B-?"),
    ("2bp_oop_pfr_turn_cbet_opp", "2bp", "oop", "pfr", "- B-?"),
    ("3bp_ip_pfr_turn_cbet_opp", "3bp", "ip", "pfr", "- B-?"),
    ("3bp_oop_pfr_turn_cbet_opp", "3bp", "oop", "pfr", "- B-?"),
    ("2bp_ip_pfc_faced_cbet_flop", "2bp", "ip", "pfc", "vs B?"),
    ("2bp_oop_pfc_faced_cbet_flop", "2bp", "oop", "pfc", "vs B?"),
    ("3bp_ip_pfc_faced_cbet_flop", "3bp", "ip", "pfc", "vs B?"),
    ("3bp_oop_pfc_faced_cbet_flop", "3bp", "oop", "pfc", "vs B?"),
    ("3bp_ip_pfc_faced_barrel_turn", "3bp", "ip", "pfc", "vs B-B?"),
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
        assert spot["measured_action"].value_counts().to_dict() == expected
