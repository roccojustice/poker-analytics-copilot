import math
import pytest
from spotlight import run_spot

pytestmark = pytest.mark.db

RANGES = {"s": (0, 45), "m": (45, 70), "l": (70, 105), "o": (105, math.inf)}
EPS = 1e-9  # f_size is a float; the SQL compares exact numerics


def hand_ids(line, role="pfc", position="oop"):
    return set(run_spot("2bp", position, role, line)["hands"]["id_hand"])


def test_size_suffixes_partition_the_unsized_line():
    full = hand_ids("vs B?")
    parts = [hand_ids(f"vs B{k}?") for k in RANGES]
    assert all(parts)
    assert set().union(*parts) == full
    assert sum(len(p) for p in parts) == len(full)


@pytest.mark.parametrize("k", RANGES)
def test_faced_bet_bucket_agrees_with_the_hand_table_size(k):
    lo, hi = RANGES[k]
    sizes = run_spot("2bp", "oop", "pfc", f"vs B{k}?")["hands"]["f_size"]
    assert ((sizes >= lo - EPS) & (sizes < hi + EPS)).all()


def test_hero_bet_label_agrees_with_the_hand_table_size():
    result = run_spot("2bp", "ip", "pfr", "- ?")
    bets = result["hands"][result["hands"]["measured_action"].str.startswith("B")]
    assert len(bets) > 0
    for label, size in zip(bets["measured_action"], bets["f_size"]):
        lo, hi = RANGES[label[1]]
        assert lo - EPS <= size < hi + EPS, (label, size)
    overall = next(r for r in result["distribution"] if r["label"] == "B")
    assert overall["hands"] == len(bets)
