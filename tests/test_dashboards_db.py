import pandas as pd
import pytest

import dashboards
import db
from filter_recipes import assemble_where
from spot_sql import PREFLOP_CONTEXTS
from spotlight import run_spot

pytestmark = pytest.mark.db
BOARD = dashboards.DASHBOARDS["2bp_ip_pfr"]


@pytest.mark.parametrize("entry", BOARD["lines"], ids=lambda e: e["id"])
def test_user_side_equals_hands_page(entry):
    mine = set(dashboards.user_matches(BOARD, entry["line"])["id_hand"])
    page = run_spot("2bp", "ip", "pfr", entry["line"], ["BB vs BTN"])["hands"]
    assert mine == (set(page["id_hand"]) if len(page) else set())


def gto_context_hands(id_player):
    where, params = assemble_where(PREFLOP_CONTEXTS[("2bp", "pfr")] + ["heads_up_flop", "ip_flop"])
    query = """SELECT chps.id_hand FROM cash_hand_player_statistics chps
               JOIN cash_hand_summary chs ON chps.id_hand = chs.id_hand
               WHERE chps.id_player = %(id_player)s""" + where
    return set(pd.read_sql(query, db.gto_engine(), params=params | {"id_player": id_player})["id_hand"])


def test_gto_preflop_context_is_the_hero_bot():
    hero = db.gto_hero_id()
    all_hero = set(pd.read_sql("SELECT id_hand FROM cash_hand_player_statistics WHERE id_player = %(p)s",
                               db.gto_engine(), params={"p": hero})["id_hand"])
    assert len(all_hero) == 1_500_000
    assert gto_context_hands(hero) == all_hero
    assert gto_context_hands(db.player_id(db.gto_engine(), "Villain")) == set()
