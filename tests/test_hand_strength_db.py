import pandas as pd
import pytest
from sqlalchemy import text

from db import engine
from hand_strength import HAND_TYPES, hand_type
from spotlight import run_spot

pytestmark = pytest.mark.db

NO_PAIR = {"Ace high", "No made hand"}
CATEGORIES = ["strflush", "fouroak", "fullhouse", "flush", "straight", "threeoak", "2pair", "1pair"]
MADE = {"strflush": "Straight flush", "fouroak": "Quads", "fullhouse": "Full house", "straight": "Straight"}
# PT4 (category, id_<s>_hand_strength, val_<s>_hole_cards_used) -> our allowed types (SCHEMA_NOTES, Session 64)
FLOP = {
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
}
MIDDLE = {"2nd pair", "3rd pair", "4th pair"}
LATER = {
    ("1pair", 0, 0): NO_PAIR,
    ("2pair", 0, 0): NO_PAIR,
    ("2pair", 5, 0): NO_PAIR,
    ("1pair", 0, 2): {"Underpair"},
    ("2pair", 4, 2): {"Underpair"},
    ("1pair", 3, 1): {"Top pair"},
    ("1pair", 1, 1): MIDDLE,
    ("1pair", 2, 1): MIDDLE,
    ("1pair", 4, 2): MIDDLE,
    ("1pair", 5, 2): MIDDLE,
    ("2pair", 1, 1): MIDDLE,
    ("2pair", 2, 1): MIDDLE,
    ("2pair", 5, 2): MIDDLE,
    ("2pair", 3, 1): {"Top pair"} | MIDDLE,
    ("1pair", 6, 2): {"Overpair"},
    ("2pair", 6, 2): {"Overpair"},
}
TRIPS = {("threeoak", 0, 0): NO_PAIR, **{("threeoak", s, 1): {"Trips"} for s in (1, 2, 3)},
         **{("threeoak", s, 2): {"Set"} for s in (4, 5, 6)}}
BOARD = {"f": 3, "t": 4, "r": 5}


def allowed(street, category, strength, used):
    if category == "flush":  # PT4 flush strength 10 = nut (SCHEMA_NOTES, Session 65)
        return NO_PAIR if used == 0 else {"Nut flush" if strength == 10 else "Other flush"}
    if category in MADE:
        return NO_PAIR if used == 0 else {MADE[category]}
    if category == "highcard":
        return NO_PAIR
    if category == "2pair" and strength in (7, 8, 9):
        return {"Two pair"}
    mapping = (FLOP if street == "f" else LATER) | TRIPS
    return mapping.get((category, strength, used), set())


def load(street):
    case = " ".join(f"WHEN c.flg_{street}_{name} THEN '{name}'" for name in CATEGORIES)
    board = [f"card_{i}" for i in range(1, BOARD[street] + 1)]
    query = text(f"""
        SELECT chps.id_hand, chps.holecard_1, chps.holecard_2, {", ".join("chs." + c for c in board)},
               CASE {case} ELSE 'highcard' END AS category,
               c.id_{street}_hand_strength AS strength, c.val_{street}_hole_cards_used AS used
        FROM cash_hand_player_statistics chps
            JOIN cash_hand_summary chs ON chs.id_hand = chps.id_hand
            JOIN cash_hand_player_combinations c ON c.id_hand = chps.id_hand AND c.id_player = chps.id_player
        WHERE chps.id_player = 10 AND chps.flg_{street}_saw""")
    df = pd.read_sql(query, engine)
    df["ours"] = [hand_type(*r) for r in df[["holecard_1", "holecard_2", *board]].itertuples(index=False)]
    return df


@pytest.fixture(scope="module", params=["f", "t", "r"])
def street_rows(request):
    return request.param, load(request.param)


def test_every_hand_agrees_with_pt4(street_rows):
    street, rows = street_rows
    ok = [ours in allowed(street, cat, s, u) for ours, cat, s, u in rows[["ours", "category", "strength", "used"]]
          .itertuples(index=False)]
    bad = rows[[not x for x in ok]]
    assert bad.empty, f"{street}: {len(bad)} of {len(rows)} disagree:\n" + bad.head(30).to_string()


def test_every_hand_type_occurs(street_rows):
    street, rows = street_rows
    missing = set(HAND_TYPES) - set(rows["ours"]) - {"Straight flush"} - ({"4th pair"} if street == "f" else set())
    assert not missing


SPOTS = [("2bp", "oop", "pfc", "vs B?"), ("2bp", "ip", "pfr", "- B-?"), ("2bp", "ip", "pfr", "- B-B-?")]


@pytest.fixture(scope="module", params=SPOTS, ids=lambda spot: spot[3])
def spot(request):
    return request.param


@pytest.fixture(scope="module")
def full(spot):
    return run_spot(*spot)


@pytest.fixture(scope="module")
def by_type(spot):
    return {t: run_spot(*spot, hand_types=[t]) for t in HAND_TYPES}


def test_single_hand_types_partition_the_result(full, by_type):
    sets = {t: set(r["hands"]["id_hand"]) if len(r["hands"]) else set() for t, r in by_type.items()}
    assert sum(len(s) for s in sets.values()) == len(set().union(*sets.values()))  # pairwise disjoint
    assert set().union(*sets.values()) == set(full["hands"]["id_hand"])
    for i, row in enumerate(full["distribution"]):
        assert sum(r["distribution"][i]["hands"] for r in by_type.values()) == row["hands"]


def test_hand_column_matches_the_filter(by_type):
    for t, result in by_type.items():
        assert (result["hands"]["hand_type"] == t).all() if len(result["hands"]) else True


def test_all_hand_types_equals_any(spot, full):
    every = run_spot(*spot, hand_types=list(HAND_TYPES))
    assert set(every["hands"]["id_hand"]) == set(full["hands"]["id_hand"])


def test_hand_split_rows_sum_to_the_result(full, by_type):
    rows = {r["hand_type"]: r["hands"] for r in full["hand_split"]}
    assert sum(rows.values()) == len(full["hands"])
    assert rows == {t: len(r["hands"]) for t, r in by_type.items() if len(r["hands"])}
