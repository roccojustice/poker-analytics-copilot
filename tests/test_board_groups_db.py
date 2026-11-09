import json
from pathlib import Path

import pytest

import dashboards
import db
from line_parser import parse_line
from spot_sql import build_spot_query

pytestmark = pytest.mark.db
BOARD = dashboards.DASHBOARDS["2bp_ip_pfr"]
SEED = {b["ranks"] for b in json.loads(Path("board_groups.json").read_text(encoding="utf-8"))["2bp_ip_pfr"][0]["boards"]}
ORDER = "AKQJT98765432"


SIDES = {
    "user": (lambda: {}, lambda: dashboards.user_matches(BOARD, "X")),
    "gto": (lambda: {"id_player": db.gto_hero_id(), "engine": db.gto_engine()}, lambda: dashboards.gto_matches(BOARD, "X")),
}


def independent_overbet_ids(db_kwargs):
    """The cbet line's hands on an overbet flop, from the raw card ids and a rule written here."""
    spec = parse_line("X", "pfr", "ip")
    where, params, measured_sql = build_spot_query("2bp", "ip", "pfr", spec, BOARD["formations"])
    raw = db.run_spot_query(where, params, measured_sql, **db_kwargs)
    keep = set()
    for row in raw[["id_hand", "card_1", "card_2", "card_3"]].itertuples(index=False):
        cards = [int(c) - 1 for c in row[1:]]
        ranks = "".join(sorted((ORDER[12 - c % 13] for c in cards), key=ORDER.index))
        if ranks in SEED and len({c // 13 for c in cards}) in (2, 3):
            keep.add(row[0])
    return keep, set(raw["id_hand"])


@pytest.mark.parametrize("side", SIDES)
def test_overbet_group_is_the_exact_set(side):
    db_kwargs, matches = SIDES[side]
    expected, everything = independent_overbet_ids(db_kwargs())
    spec = parse_line("X", "pfr", "ip")
    kept = {negate: set(dashboards.side_matches(matches(), spec, {}, (),
                                                dashboards.group_pick("2bp_ip_pfr", {"name": "overbet",
                                                                                     "negate": negate}))["id_hand"])
            for negate in (False, True)}
    assert expected and kept[False] == expected
    assert kept[True] == everything - expected
