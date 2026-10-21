import pandas as pd
import pytest
from sqlalchemy import text

from db import engine
from hand_strength import HAND_TYPES, hand_type
from spotlight import run_spot

pytestmark = pytest.mark.db

NO_PAIR = {"Ace high", "No made hand"}
CATEGORIES = ["strflush", "fouroak", "fullhouse", "flush", "straight", "threeoak", "2pair", "1pair"]
MADE = {"strflush": "Straight flush", "fouroak": "Quads", "fullhouse": "Full house", "flush": "Flush",
        "straight": "Straight"}
# PT4 (category, id_f_hand_strength, val_f_hole_cards_used) -> our allowed types (SCHEMA_NOTES, Session 64)
MAPPING = {
    ("1pair", 0, 0): NO_PAIR,
    ("1pair", 0, 2): {"Underpair"},
    ("1pair", 1, 1): {"3rd pair"},
    ("1pair", 2, 1): {"2nd pair"},
    ("1pair", 3, 1): {"Top pair"},
    ("1pair", 4, 2): {"3rd pair"},
    ("1pair", 5, 2): {"2nd pair"},
    ("1pair", 6, 2): {"Overpair"},
    ("2pair", 3, 1): {"Top pair", "2nd pair"},
    ("2pair", 4, 2): {"Underpair"},
    ("2pair", 5, 2): {"2nd pair"},
    ("2pair", 6, 2): {"Overpair"},
    ("threeoak", 0, 0): NO_PAIR,
    ("threeoak", 1, 1): {"Trips"},
    ("threeoak", 3, 1): {"Trips"},
    ("threeoak", 4, 2): {"Set"},
    ("threeoak", 5, 2): {"Set"},
    ("threeoak", 6, 2): {"Set"},
}


def allowed(category, strength, used):
    if category in MADE:
        return {MADE[category]}
    if category == "highcard":
        return NO_PAIR
    if category == "2pair" and strength in (7, 8, 9):
        return {"Two pair"}
    return MAPPING.get((category, strength, used), set())


@pytest.fixture(scope="module")
def rows():
    case = " ".join(f"WHEN c.flg_f_{name} THEN '{name}'" for name in CATEGORIES)
    query = text(f"""
        SELECT chps.id_hand, chps.holecard_1, chps.holecard_2, chs.card_1, chs.card_2, chs.card_3,
               CASE {case} ELSE 'highcard' END AS category,
               c.id_f_hand_strength AS strength, c.val_f_hole_cards_used AS used
        FROM cash_hand_player_statistics chps
            JOIN cash_hand_summary chs ON chs.id_hand = chps.id_hand
            JOIN cash_hand_player_combinations c ON c.id_hand = chps.id_hand AND c.id_player = chps.id_player
        WHERE chps.id_player = 10 AND chps.flg_f_saw""")
    df = pd.read_sql(query, engine)
    df["ours"] = [hand_type(*r) for r in df[["holecard_1", "holecard_2", "card_1", "card_2", "card_3"]]
                  .itertuples(index=False)]
    return df


def test_every_flop_hand_agrees_with_pt4(rows):
    ok = [ours in allowed(cat, s, u) for ours, cat, s, u in rows[["ours", "category", "strength", "used"]]
          .itertuples(index=False)]
    bad = rows[[not x for x in ok]]
    assert bad.empty, f"{len(bad)} of {len(rows)} disagree:\n" + bad.head(30).to_string()


def test_every_hand_type_occurs(rows):
    missing = set(HAND_TYPES) - set(rows["ours"]) - {"Straight flush"}
    assert not missing


SPOT = ("2bp", "oop", "pfc", "vs B?")


@pytest.fixture(scope="module")
def full():
    return run_spot(*SPOT)


@pytest.fixture(scope="module")
def by_type():
    return {t: run_spot(*SPOT, hand_types=[t]) for t in HAND_TYPES}


def test_single_hand_types_partition_the_result(full, by_type):
    sets = {t: set(r["hands"]["id_hand"]) if len(r["hands"]) else set() for t, r in by_type.items()}
    assert sum(len(s) for s in sets.values()) == len(set().union(*sets.values()))  # pairwise disjoint
    assert set().union(*sets.values()) == set(full["hands"]["id_hand"])
    for i, row in enumerate(full["distribution"]):
        assert sum(r["distribution"][i]["hands"] for r in by_type.values()) == row["hands"]


def test_hand_column_matches_the_filter(by_type):
    for t, result in by_type.items():
        assert (result["hands"]["hand_type"] == t).all() if len(result["hands"]) else True


def test_all_hand_types_equals_any(full):
    every = run_spot(*SPOT, hand_types=list(HAND_TYPES))
    assert set(every["hands"]["id_hand"]) == set(full["hands"]["id_hand"])


def test_hand_split_rows_sum_to_the_result(full, by_type):
    rows = {r["hand_type"]: r["hands"] for r in full["hand_split"]}
    assert sum(rows.values()) == len(full["hands"])
    assert rows == {t: len(r["hands"]) for t, r in by_type.items() if len(r["hands"])}
