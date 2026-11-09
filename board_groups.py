"""User-defined groups of flops, per dashboard: stored in board_groups.json, matched on flop ranks + texture."""
import json
import os
from pathlib import Path

import pandas as pd

from board_types import RANKS
from line_parser import SpotInputError

GROUPS_FILE = Path("board_groups.json")
TEXTURES = ("rainbow", "two-tone")


def _read():
    if not GROUPS_FILE.exists():
        return {}
    return json.loads(GROUPS_FILE.read_text(encoding="utf-8"))


def load(dashboard_id):
    return normalize(_read().get(dashboard_id, []))  # a hand-edited "98j" still matches


def _ranks(raw):
    ranks = str(raw).strip().upper()
    if len(ranks) != 3 or any(r not in RANKS for r in ranks):
        raise SpotInputError(f"A board is three ranks (e.g. J98): {raw!r}")
    return "".join(sorted(ranks, key=RANKS.index, reverse=True))


def _textures(raw, ranks):
    textures = set(raw or ())
    if not textures or textures - set(TEXTURES):
        raise SpotInputError(f"{ranks}: textures are rainbow and/or two-tone")
    if len(set(ranks)) == 1:
        if "rainbow" not in textures:
            raise SpotInputError(f"{ranks}: trips are always rainbow")
        textures = {"rainbow"}  # both ticked = any texture, and trips have only one
    return textures


def _group(raw):
    name = str(raw.get("name", "")).strip()
    if not name:
        raise SpotInputError("A board group needs a name")
    if "boards" not in raw:
        raise SpotInputError(f"{name}: no boards list")
    merged = {}
    for board in raw["boards"]:
        ranks = _ranks(board.get("ranks", ""))
        merged.setdefault(ranks, set()).update(_textures(board.get("textures"), ranks))
    boards = [{"ranks": ranks, "textures": [t for t in TEXTURES if t in textures]}
              for ranks, textures in merged.items()]
    return {"name": name, "boards": boards}


def normalize(groups):
    """Validated, canonical groups: ranks high to low, textures in TEXTURES order, repeated boards merged."""
    out = [_group(raw) for raw in groups]
    names = [g["name"].lower() for g in out]
    if len(names) != len(set(names)):
        raise SpotInputError("Two board groups have the same name")
    return out


def save(dashboard_id, groups):
    groups = normalize(groups)
    data = _read() | {dashboard_id: groups}
    partial = GROUPS_FILE.with_suffix(".partial")
    try:
        partial.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        os.replace(partial, GROUPS_FILE)  # atomic: a reader sees the old file or the whole new one
    finally:
        partial.unlink(missing_ok=True)
    return groups


def find(dashboard_id, name):
    group = next((g for g in load(dashboard_id) if g["name"] == name), None)
    if group is None:
        raise SpotInputError(f"Unknown board group: {name}")
    return group


def in_group(matches, group):
    """True for the hands whose flop ranks + texture is one of the group's boards."""
    keys = {f"{b['ranks']}|{t}" for b in group["boards"] for t in b["textures"]}
    hand_keys = matches["flop_ranks"].astype(str) + "|" + matches["flop_texture"].astype(str)
    return pd.Series(hand_keys.isin(keys), index=matches.index)
