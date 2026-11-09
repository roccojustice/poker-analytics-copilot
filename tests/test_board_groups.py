import json
from pathlib import Path

import pandas as pd
import pytest

import board_groups
from line_parser import SpotInputError


@pytest.fixture
def groups_file(monkeypatch, tmp_path):
    path = tmp_path / "g.json"
    monkeypatch.setattr("board_groups.GROUPS_FILE", path)
    return path


def test_missing_file_has_no_groups(groups_file):
    assert board_groups.load("2bp_ip_pfr") == []


def test_save_round_trips_and_keeps_other_dashboards(groups_file):
    board_groups.save("other", [{"name": "x", "boards": [{"ranks": "AK2", "textures": ["rainbow"]}]}])
    board_groups.save("2bp_ip_pfr", [{"name": "overbet",
                                      "boards": [{"ranks": "98j", "textures": ["two-tone", "rainbow"]}]}])
    assert board_groups.load("2bp_ip_pfr") == [
        {"name": "overbet", "boards": [{"ranks": "J98", "textures": ["rainbow", "two-tone"]}]}]
    assert board_groups.load("other")[0]["name"] == "x"


def test_duplicate_board_merges_textures():
    out = board_groups.normalize([{"name": "g", "boards": [{"ranks": "J98", "textures": ["rainbow"]},
                                                           {"ranks": "98J", "textures": ["two-tone"]}]}])
    assert out[0]["boards"] == [{"ranks": "J98", "textures": ["rainbow", "two-tone"]}]


@pytest.mark.parametrize("groups", [
    [{"name": "", "boards": []}],
    [{"name": "  ", "boards": []}],
    [{"name": "a", "boards": []}, {"name": "A", "boards": []}],
    [{"name": "g", "boards": [{"ranks": "J9", "textures": ["rainbow"]}]}],
    [{"name": "g", "boards": [{"ranks": "J9X", "textures": ["rainbow"]}]}],
    [{"name": "g", "boards": [{"ranks": "J98", "textures": []}]}],
    [{"name": "g", "boards": [{"ranks": "J98", "textures": ["monotone"]}]}],
    [{"name": "g", "boards": [{"ranks": "JJJ", "textures": ["two-tone"]}]}],
    [{"name": "g"}],
    [{"name": "g", "boards": [{"ranks": "J98"}]}],
])
def test_bad_groups_error(groups):
    with pytest.raises(SpotInputError):
        board_groups.normalize(groups)


def test_failed_write_keeps_the_old_file(groups_file, monkeypatch):
    board_groups.save("2bp_ip_pfr", [{"name": "old", "boards": []}])

    def broken(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("board_groups.os.replace", broken)
    with pytest.raises(OSError):
        board_groups.save("2bp_ip_pfr", [{"name": "new", "boards": []}])
    assert board_groups.load("2bp_ip_pfr")[0]["name"] == "old"
    assert list(groups_file.parent.glob("*.partial")) == []


def test_find_by_name(groups_file):
    board_groups.save("2bp_ip_pfr", [{"name": "overbet", "boards": []}])
    assert board_groups.find("2bp_ip_pfr", "overbet")["name"] == "overbet"


def test_unknown_group_errors(groups_file):
    with pytest.raises(SpotInputError, match="nope"):
        board_groups.find("2bp_ip_pfr", "nope")


GROUP = {"name": "g", "boards": [{"ranks": "J98", "textures": ["rainbow", "two-tone"]},
                                 {"ranks": "Q96", "textures": ["rainbow"]}]}
FLOPS = pd.DataFrame({"flop_ranks": ["J98", "J98", "J98", "Q96", "Q96"],
                      "flop_texture": ["rainbow", "two-tone", "monotone", "two-tone", "rainbow"]})


def test_membership_by_ranks_and_texture():
    assert list(board_groups.in_group(FLOPS, GROUP)) == [True, True, False, False, True]


def test_membership_on_category_columns():
    assert list(board_groups.in_group(FLOPS.astype("category"), GROUP)) == [True, True, False, False, True]


def test_empty_group_matches_nothing():
    assert not board_groups.in_group(FLOPS, {"name": "g", "boards": []}).any()


def test_seed_file_is_valid_and_has_overbet():
    data = json.loads(Path("board_groups.json").read_text(encoding="utf-8"))
    assert board_groups.normalize(data["2bp_ip_pfr"]) == data["2bp_ip_pfr"]
    overbet = data["2bp_ip_pfr"][0]
    assert overbet["name"] == "overbet" and len(overbet["boards"]) == 24
    assert all(b["textures"] == ["rainbow", "two-tone"] for b in overbet["boards"])
