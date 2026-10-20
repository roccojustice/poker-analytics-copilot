import pytest

from board_types import RIVER_LABELS, TURN_LABELS
from spotlight import run_spot

pytestmark = pytest.mark.db

MADE = ["FC", "SC", "BP high", "BP mid", "BP low", "BW A", "BW K", "BW Q", "BW J"]
TURN_LINE = ("2bp", "ip", "pfr", "- B-?")
RIVER_LINE = ("2bp", "ip", "pfr", "- B-B-?")


def ids(*args, **kwargs):
    return set(run_spot(*args, **kwargs)["hands"]["id_hand"])


@pytest.mark.parametrize("line, key", [(TURN_LINE, "turn_types"), (RIVER_LINE, "river_types")])
def test_brick_vs_rest_partitions(line, key):
    bricks, made = ids(*line, **{key: ["Brick"]}), ids(*line, **{key: MADE})
    assert bricks and made
    assert not bricks & made
    assert bricks | made == ids(*line)


def test_hand_column_contains_filtered_label():
    for label in TURN_LABELS:
        hands = run_spot(*TURN_LINE, turn_types=[label])["hands"]
        assert all(label in labels.split(", ") for labels in hands["turn_type"]), label


def test_all_labels_equals_any():
    assert ids(*TURN_LINE, turn_types=list(TURN_LABELS)) == ids(*TURN_LINE)
    assert ids(*RIVER_LINE, river_types=list(RIVER_LABELS)) == ids(*RIVER_LINE)
