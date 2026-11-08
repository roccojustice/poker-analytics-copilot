import pandas as pd
import pytest

import dashboards
from line_parser import SpotInputError, parse_line


def frame(letters, flop_type="Low", turn_type="Brick", hand_type="Air", draw_type="No draw"):
    return pd.DataFrame({
        "id_hand": range(1, len(letters) + 1), "measured_action": letters,
        "flop_type": flop_type, "turn_type": turn_type, "river_type": None,
        "hand_type": hand_type, "draw_type": draw_type,
    })


@pytest.fixture
def sides(monkeypatch):
    """user / gto frames per Line; unknown Lines get an empty frame."""
    data = {"user": {}, "gto": {}}
    monkeypatch.setattr("dashboards.user_matches",
                        lambda dashboard, line, date_from=None, date_to=None: data["user"].get(line, frame([])))
    monkeypatch.setattr("dashboards.line_matches",
                        lambda pot, position, role, line, formations: data["gto"].get(line, frame([])))
    return data


def row(rows, row_id):
    return next(r for r in rows if r["id"] == row_id)


def pct(side, label):
    return next(r["pct"] for r in side["distribution"] if r["label"] == label)


def test_rows_follow_the_registry_order(sides):
    rows = dashboards.dashboard_rows("2bp_ip_pfr")
    assert [r["id"] for r in rows] == [l["id"] for l in dashboards.DASHBOARDS["2bp_ip_pfr"]["lines"]]


def test_gap_is_user_minus_gto(sides):
    sides["user"]["X"] = frame(["Bs", "Bs", "X", "X", "X"])            # B 40%
    sides["gto"]["X"] = frame(["Bs"] * 52 + ["X"] * 48)                  # B 52%
    cbet = row(dashboards.dashboard_rows("2bp_ip_pfr"), "cbet_flop")
    assert cbet["user"]["hands"] == 5 and cbet["gto"]["hands"] == 100
    assert pct(cbet["user"], "B") == 40.0 and pct(cbet["gto"], "B") == 52.0
    assert cbet["gap"]["B"] == -12.0


def test_zero_hands_side_gives_none_gap(sides):
    sides["gto"]["XR-B"] = frame(["Fs", "Cs"])
    vs = row(dashboards.dashboard_rows("2bp_ip_pfr"), "vs_xr_b")
    assert vs["user"]["hands"] == 0
    assert all(gap is None for gap in vs["gap"].values())


def test_flop_filter_applies_to_both_sides(sides):
    sides["user"]["X"] = pd.concat([frame(["Bs"]), frame(["X"], flop_type="High")])
    sides["gto"]["X"] = pd.concat([frame(["X"]), frame(["Bs"], flop_type="High")])
    cbet = row(dashboards.dashboard_rows("2bp_ip_pfr", flop_types=["Low"]), "cbet_flop")
    assert pct(cbet["user"], "B") == 100.0 and pct(cbet["gto"], "B") == 0.0


def test_turn_filter_blanks_flop_rows(sides):
    sides["user"]["X"] = frame(["Bs"])
    rows = dashboards.dashboard_rows("2bp_ip_pfr", turn_types=["Brick"])
    cbet, probe = row(rows, "cbet_flop"), row(rows, "vs_probe_turn")
    assert cbet["user"] is None and cbet["gto"] is None and "turn" in cbet["reason"].lower()
    assert probe["reason"] is None


def test_faced_size_filters_response_rows_only(sides):
    sides["user"]["X-B"] = frame(["Fs", "Cs", "Fl"])
    sides["user"]["X"] = frame(["Bs", "X"])
    rows = dashboards.dashboard_rows("2bp_ip_pfr", faced_sizes=["S"])
    probe, cbet = row(rows, "vs_probe_turn"), row(rows, "cbet_flop")
    assert probe["user"]["hands"] == 2 and not probe["size_filter_ignored"]
    assert cbet["user"]["hands"] == 2 and cbet["size_filter_ignored"]


def test_bet_rows_split_by_size(sides):
    sides["user"]["X"] = frame(["Bs", "Bl", "X", "X"])
    cbet = row(dashboards.dashboard_rows("2bp_ip_pfr"), "cbet_flop")
    assert pct(cbet["user"], "Bs") == 25.0 and pct(cbet["user"], "Bl") == 25.0


def test_date_range_reaches_the_user_side_only(sides, monkeypatch):
    seen = {}
    monkeypatch.setattr("dashboards.user_matches",
                        lambda dashboard, line, date_from=None, date_to=None: seen.update(d=date_from) or frame([]))
    dashboards.dashboard_rows("2bp_ip_pfr", date_from="2026-01-01")
    assert seen["d"] == "2026-01-01"


def test_unknown_dashboard_or_size_errors(sides):
    with pytest.raises(SpotInputError):
        dashboards.dashboard_rows("nope")
    with pytest.raises(SpotInputError):
        dashboards.dashboard_rows("2bp_ip_pfr", faced_sizes=["XL"])


def test_every_registry_line_parses():
    for board in dashboards.DASHBOARDS.values():
        for line in board["lines"]:
            parse_line(line["line"], board["role"], board["position"])
