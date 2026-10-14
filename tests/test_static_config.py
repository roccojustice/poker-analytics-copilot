import json
import re
from pathlib import Path

from line_parser import parse_line
from spot_sql import FORMATIONS

INDEX = Path(__file__).resolve().parent.parent / "static" / "index.html"


def load_config():
    html = INDEX.read_text(encoding="utf-8")
    match = re.search(r'<script type="application/json" id="spot-config">(.*?)</script>', html, re.S)
    assert match, "index.html has no spot-config block"
    return json.loads(match.group(1))


def test_formations_match_the_backend():
    assert load_config()["formations"] == FORMATIONS


def test_presets_are_the_20_v1_lines_and_all_parse():
    presets = load_config()["presets"]
    assert sum(len(lines) for lines in presets.values()) == 20
    for context, lines in presets.items():
        pot, position, role = context.split()
        assert pot in ("2bp", "3bp")
        for line in lines:
            parse_line(line, role, position)  # raises SpotInputError if a preset is malformed
