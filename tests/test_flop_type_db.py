from collections import Counter
import pytest
from board_types import FLOP_TYPES
from spotlight import run_spot

pytestmark = pytest.mark.db

SPOT = ("2bp", "oop", "pfc", "vs B?")


@pytest.fixture(scope="module")
def full():
    return run_spot(*SPOT)


@pytest.fixture(scope="module")
def by_type():
    return {t: run_spot(*SPOT, flop_types=[t]) for t in FLOP_TYPES}


def test_single_types_partition_the_result(full, by_type):
    sets = {t: set(r["hands"]["id_hand"]) if len(r["hands"]) else set() for t, r in by_type.items()}
    assert sum(len(s) for s in sets.values()) == len(set().union(*sets.values()))  # pairwise disjoint
    assert set().union(*sets.values()) == set(full["hands"]["id_hand"])
    for i, row in enumerate(full["distribution"]):
        assert sum(r["distribution"][i]["hands"] for r in by_type.values()) == row["hands"]


def test_hand_column_matches_the_filter(full, by_type):
    for t, result in by_type.items():
        assert (result["hands"]["flop_type"] == t).all() if len(result["hands"]) else True
    sizes = {t: len(r["hands"]) for t, r in by_type.items() if len(r["hands"])}
    assert Counter(full["hands"]["flop_type"]) == sizes


def test_all_types_equals_any(full):
    every = run_spot(*SPOT, flop_types=list(FLOP_TYPES))
    assert set(every["hands"]["id_hand"]) == set(full["hands"]["id_hand"])
