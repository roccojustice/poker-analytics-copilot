import pytest
from line_parser import parse_line
from spotlight import run_spot

pytestmark = pytest.mark.db

SPOTS = [("2bp", "oop", "pfc", "vs B?"), ("2bp", "ip", "pfr", "- B?"), ("3bp", "ip", "pfc", "vs B-B?")]
ACTIONS = ("F", "C", "R")


def ids_labelled(hands, label):
    return set(hands.loc[hands["measured_action"] == label, "id_hand"])


@pytest.mark.parametrize("pot, position, role, line", SPOTS)
def test_split_cells_sum_to_the_distribution(pot, position, role, line):
    result = run_spot(pot, position, role, line)
    by_action = {row["action"]: row["hands"] for row in result["distribution"]}
    for i, action in enumerate(ACTIONS):
        assert sum(row["cells"][i]["hands"] for row in result["split"]) == by_action[action]
    assert sum(row["hands"] for row in result["split"]) == len(result["hands"]) > 0


@pytest.mark.parametrize("key", "smlo")
@pytest.mark.parametrize("pot, position, role, line", SPOTS)
def test_sized_labels_equal_the_suffixed_line(pot, position, role, line, key):
    prefix = parse_line(line, role, position).decision.hero
    unsized = run_spot(pot, position, role, line)["hands"]
    suffixed = run_spot(pot, position, role, line.replace("?", f"{key}?"))["hands"]
    for action in ACTIONS:
        split_ids = ids_labelled(unsized, prefix + action + key) if len(unsized) else set()
        line_ids = ids_labelled(suffixed, prefix + action) if len(suffixed) else set()
        extra, missing = split_ids - line_ids, line_ids - split_ids
        assert not extra and not missing, (
            f"{line} {action}{key}: {len(extra)} extra {sorted(extra)[:10]}, "
            f"{len(missing)} missing {sorted(missing)[:10]}"
        )
