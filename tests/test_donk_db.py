import pandas as pd
import pytest

from db import engine
from spotlight import run_spot

pytestmark = pytest.mark.db


def donk_flags(hands, street):
    ids = [int(i) for i in hands["id_hand"]]
    flags = pd.read_sql(
        f"SELECT flg_{street}_donk_def_opp AS flag FROM cash_hand_player_statistics"
        " WHERE id_player = 10 AND id_hand = ANY(%(ids)s)",
        engine,
        params={"ids": ids},
    )
    return flags["flag"]


@pytest.mark.parametrize("pot, line, street, expected", [
    ("2bp", "XC-D", "t", True),
    ("3bp", "XC-D", "t", True),
    ("2bp", "XC-XC-D", "r", True),
    ("3bp", "XC-XC-D", "r", True),
    ("2bp", "XR-B", "t", False),
    ("3bp", "XR-B", "t", False),
    ("2bp", "X-B", "t", False),
    ("3bp", "X-B", "t", False),
    ("2bp", "XC-X-B", "r", False),
])
def test_d_matches_pt4_donk_flag(pot, line, street, expected):
    hands = run_spot(pot, "ip", "pfr", line)["hands"]
    assert len(hands) > 0
    assert donk_flags(hands, street).eq(expected).all()
