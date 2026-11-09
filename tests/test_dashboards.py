import pandas as pd
import pytest

import dashboards
from line_parser import SpotInputError, parse_line


def frame(letters, flop_type="Low", turn_type="Brick", hand_type="No made hand", draw_type="No draw",
          flop_ranks="J98", flop_texture="rainbow"):
    return pd.DataFrame({
        "id_hand": range(1, len(letters) + 1), "measured_action": letters,
        "flop_type": flop_type, "flop_ranks": flop_ranks, "flop_texture": flop_texture,
        "turn_type": turn_type, "river_type": None,
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


@pytest.fixture
def details(monkeypatch):
    calls = []

    def fake(id_hands, id_player=None, engine=None):
        calls.append({"ids": list(id_hands), "id_player": id_player})
        return pd.DataFrame({"id_hand": list(id_hands)})

    monkeypatch.setattr("dashboards.get_hand_details", fake)
    monkeypatch.setattr("dashboards.gto_hero_id", lambda: 99)
    monkeypatch.setattr("dashboards.gto_engine", lambda: None)
    return calls


def test_detail_has_both_sides_with_the_same_shape(sides, details):
    sides["user"]["X-B"] = frame(["Fs", "Cl"], hand_type="Top pair Gk")
    sides["gto"]["X-B"] = frame(["Fs", "Fs", "Cl"], hand_type="Overpair")
    out = dashboards.line_detail("2bp_ip_pfr", "vs_probe_turn")
    assert out["line"]["line"] == "X-B"
    for name, total in [("user", 2), ("gto", 3)]:
        detail = out[name]
        assert detail["hands_total"] == total
        assert set(detail) == {"hands_total", "distribution", "split", "hand_split", "draw_split", "hands"}
        assert detail["split"] is not None
    assert [r["hand_type"] for r in out["gto"]["hand_split"]] == ["Overpair"]


def test_gto_hands_capped_at_200_with_total(sides, details):
    sides["gto"]["X"] = frame(["X"] * 250)
    out = dashboards.line_detail("2bp_ip_pfr", "cbet_flop")
    assert out["gto"]["hands_total"] == 250 and len(out["gto"]["hands"]) == 200
    assert details[-1]["id_player"] == 99


def test_hand_pick_filters_both_sides(sides, details):
    sides["user"]["X"] = pd.concat([frame(["Bs"], hand_type="Overpair"), frame(["X"])])
    sides["gto"]["X"] = pd.concat([frame(["X"], hand_type="Overpair"), frame(["Bs"])])
    out = dashboards.line_detail("2bp_ip_pfr", "cbet_flop", hand_types=["Overpair"])
    assert out["user"]["hands_total"] == 1 and out["gto"]["hands_total"] == 1
    assert pct(out["user"], "B") == 100.0 and pct(out["gto"], "B") == 0.0
    assert {r["hand_type"] for r in out["user"]["hand_split"]} == {"Overpair", "No made hand"}


def test_unknown_line_id_errors(sides, details):
    with pytest.raises(SpotInputError):
        dashboards.line_detail("2bp_ip_pfr", "nope")


def test_user_side_is_reused_for_ten_minutes(monkeypatch):
    queries = []
    monkeypatch.setattr("dashboards.run_spot_query",
                        lambda where, params, measured_sql: queries.append(1) or frame_cards())
    now = [1000.0]
    monkeypatch.setattr("dashboards.time.monotonic", lambda: now[0])
    dashboards._user_cache.clear()
    board = dashboards.DASHBOARDS["2bp_ip_pfr"]
    dashboards.user_matches(board, "X")
    dashboards.user_matches(board, "X")
    assert len(queries) == 1
    now[0] += 601
    dashboards.user_matches(board, "X")
    assert len(queries) == 2


def frame_cards():
    from test_spotlight import fake_matches
    return fake_matches([(1, "Bs")])


def test_a_side_with_no_hands_has_no_pct(sides, details):
    sides["gto"]["X-B"] = frame(["Fs", "Cs"])
    vs = row(dashboards.dashboard_rows("2bp_ip_pfr"), "vs_probe_turn")
    assert all(r["pct"] is None for r in vs["user"]["distribution"])
    out = dashboards.line_detail("2bp_ip_pfr", "vs_probe_turn")
    assert all(r["pct"] is None for r in out["user"]["distribution"])
    large = next(r for r in out["gto"]["split"] if r["size"] == "L")  # GTO never faced a large bet here
    assert all(cell["pct"] is None for cell in large["cells"])


def test_action_pick_filters_hands_and_type_tables_not_the_action_table(sides, details):
    sides["user"]["X"] = pd.concat([frame(["Bs"], hand_type="Overpair"), frame(["Bl"]), frame(["X"])])
    sides["gto"]["X"] = pd.concat([frame(["X"], hand_type="Overpair"), frame(["Bs", "Bs"])])
    out = dashboards.line_detail("2bp_ip_pfr", "cbet_flop", actions=["B"])
    assert out["user"]["hands_total"] == 2 and out["gto"]["hands_total"] == 2
    assert {h["measured_action"] for h in out["user"]["hands"]} == {"Bs", "Bl"}
    assert pct(out["user"], "X") == 33.3  # the action table ignores its own picks
    assert {r["hand_type"]: r["hands"] for r in out["user"]["hand_split"]} == {"Overpair": 1, "No made hand": 1}
    assert [r["draw_type"] for r in out["gto"]["draw_split"]] == ["No draw"]


def test_size_pick_keeps_that_size_only_and_picks_or_together(sides, details):
    sides["user"]["X"] = frame(["Bs", "Bl", "Bo", "X"])
    sides["gto"]["X"] = frame(["Bs"])
    assert dashboards.line_detail("2bp_ip_pfr", "cbet_flop", actions=["Bl"])["user"]["hands_total"] == 1
    out = dashboards.line_detail("2bp_ip_pfr", "cbet_flop", actions=["Bl", "X"])
    assert {h["measured_action"] for h in out["user"]["hands"]} == {"Bl", "X"}


def test_action_pick_with_a_hand_pick_is_and(sides, details):
    sides["user"]["X"] = pd.concat([frame(["Bs"], hand_type="Overpair"), frame(["X"], hand_type="Overpair"),
                                    frame(["Bs"])])
    sides["gto"]["X"] = frame(["Bs"])
    out = dashboards.line_detail("2bp_ip_pfr", "cbet_flop", actions=["B"], hand_types=["Overpair"])
    assert out["user"]["hands_total"] == 1
    assert pct(out["user"], "B") == 50.0  # Overpair hands only, both actions


def test_response_pick_matches_every_faced_size(sides, details):
    sides["user"]["X-B"] = frame(["Fs", "Cl", "Cs"])
    sides["gto"]["X-B"] = frame(["Fs"])
    out = dashboards.line_detail("2bp_ip_pfr", "vs_probe_turn", actions=["C"])
    assert out["user"]["hands_total"] == 2


def test_unknown_action_pick_errors(sides, details):
    with pytest.raises(SpotInputError):
        dashboards.line_detail("2bp_ip_pfr", "cbet_flop", actions=["Q"])


@pytest.fixture
def groups(monkeypatch, tmp_path):
    monkeypatch.setattr("board_groups.GROUPS_FILE", tmp_path / "g.json")
    dashboards.save_groups("2bp_ip_pfr", [{"name": "g", "boards": [{"ranks": "J98", "textures": ["rainbow"]}]}])


def mixed():
    return pd.concat([frame(["Bs"]), frame(["X"], flop_ranks="Q96")]).assign(id_hand=[1, 2])


def test_group_pick_filters_both_sides(sides, groups):
    sides["user"]["X"] = mixed()
    sides["gto"]["X"] = mixed()
    cbet = row(dashboards.dashboard_rows("2bp_ip_pfr", board_group={"name": "g", "negate": False}), "cbet_flop")
    assert pct(cbet["user"], "B") == 100.0 and pct(cbet["gto"], "B") == 100.0
    cbet = row(dashboards.dashboard_rows("2bp_ip_pfr", board_group={"name": "g", "negate": True}), "cbet_flop")
    assert pct(cbet["user"], "B") == 0.0 and pct(cbet["gto"], "B") == 0.0


def test_negated_group_is_the_exact_complement(groups):
    spec = parse_line("X", "pfr", "ip")
    matches = pd.concat([frame(["X"] * 3), frame(["X"] * 2, flop_ranks="Q96"),
                         frame(["X"], flop_texture="two-tone")]).assign(id_hand=range(6))
    kept = {negate: set(dashboards.side_matches(matches, spec, {}, (),
                                                dashboards.group_pick("2bp_ip_pfr", {"name": "g", "negate": negate}))
                        ["id_hand"]) for negate in (False, True)}
    assert kept[False] == {0, 1, 2} and kept[False] | kept[True] == set(range(6)) and not kept[False] & kept[True]


def test_group_pick_reaches_line_detail(sides, details, groups):
    sides["user"]["X"] = mixed()
    sides["gto"]["X"] = mixed()
    out = dashboards.line_detail("2bp_ip_pfr", "cbet_flop", board_group={"name": "g", "negate": False})
    assert out["user"]["hands_total"] == 1 and out["gto"]["hands_total"] == 1


def test_no_group_pick_keeps_every_hand(sides, groups):
    sides["user"]["X"] = mixed()
    cbet = row(dashboards.dashboard_rows("2bp_ip_pfr"), "cbet_flop")
    assert cbet["user"]["hands"] == 2


def test_unknown_group_pick_errors(sides, groups):
    with pytest.raises(SpotInputError, match="gone"):
        dashboards.dashboard_rows("2bp_ip_pfr", board_group={"name": "gone", "negate": False})


def test_save_groups_rejects_an_unknown_dashboard(groups):
    with pytest.raises(SpotInputError):
        dashboards.save_groups("nope", [])
