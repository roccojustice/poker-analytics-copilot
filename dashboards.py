"""GTO dashboards: per spot, the user's frequencies next to the GTO bot DB's, line by line."""
from board_types import FLOP_TYPES, RIVER_LABELS, TURN_LABELS
from db import run_spot_query
from gto_cache import line_matches
from line_parser import SpotInputError, parse_line
from sizing import SIZE_BUCKETS
from spot_sql import build_spot_query, splits_by_size
from spotlight import _checked, _distribution, classify, filter_types

DASHBOARDS = {
    "2bp_ip_pfr": {
        "name": "2BP IP PFR", "pot": "2bp", "position": "ip", "role": "pfr", "formations": ["BB vs BTN"],
        "lines": [
            {"id": "cbet_flop", "name": "Cbet flop", "line": "X"},
            {"id": "double_barrel", "name": "Double barrel", "line": "XC-X"},
            {"id": "triple_barrel", "name": "Triple barrel", "line": "XC-XC-X"},
            {"id": "vs_xr_flop", "name": "vs XR flop", "line": "XR"},
            {"id": "vs_probe_turn", "name": "vs probe turn", "line": "X-B"},
            {"id": "delayed_cbet", "name": "Delayed cbet turn", "line": "X-X"},
            {"id": "vs_xr_b", "name": "vs XR-B", "line": "XR-B"},
            {"id": "vs_donk_turn", "name": "vs donk turn", "line": "XC-D"},
        ],
    },
}


def dashboard(dashboard_id):
    if dashboard_id not in DASHBOARDS:
        raise SpotInputError(f"Unknown dashboard: {dashboard_id}")
    return DASHBOARDS[dashboard_id]


def user_matches(board, line, date_from=None, date_to=None):
    """The user's hands for a Line, live from the user DB, classified like the GTO side."""
    spec = parse_line(line, board["role"], board["position"])
    where, params, measured_sql = build_spot_query(board["pot"], board["position"], board["role"], spec,
                                                   board["formations"], date_from, date_to)
    return classify(run_spot_query(where, params, measured_sql), spec.decision.street)


def gto_matches(board, line):
    return line_matches(board["pot"], board["position"], board["role"], line, board["formations"])


def blank_reason(street, turn_types, river_types):
    if turn_types and street == "f":
        return "Turn filter needs a turn or river decision"
    if river_types and street != "r":
        return "River filter needs a river decision"
    return None


def side_matches(matches, spec, filters, faced_sizes):
    """Applies the type filters and, on a response to a bet, the faced-size filter."""
    matches = filter_types(matches, **filters)
    if faced_sizes and splits_by_size(spec):
        size_letters = [s.lower() for s in faced_sizes]
        matches = matches[matches["measured_action"].astype(str).str[-1].isin(size_letters)]
    return matches


def labels(matches, spec):
    """measured_action -> the hands page's labels: decision prefix + letter (+ size letter on bets)."""
    prefix = spec.decision.hero
    full = prefix + matches["measured_action"].astype(str)
    return full, (full.str[:len(prefix) + 1] if splits_by_size(spec) else full)


def side(matches, spec):
    _, unsized = labels(matches, spec)
    return {"hands": len(matches), "distribution": _distribution(unsized, spec.measured, spec.decision.hero)}


def gap(user, gto):
    if not user["hands"] or not gto["hands"]:
        return {r["label"]: None for r in user["distribution"]}
    gto_pct = {r["label"]: r["pct"] for r in gto["distribution"]}
    return {r["label"]: round(r["pct"] - gto_pct[r["label"]], 1) for r in user["distribution"]}


def check_filters(flop_types, turn_types, river_types, faced_sizes):
    _checked(faced_sizes, SIZE_BUCKETS, "size")
    return {"flop_types": _checked(flop_types, FLOP_TYPES, "flop type"),
            "turn_types": _checked(turn_types, TURN_LABELS, "turn type"),
            "river_types": _checked(river_types, RIVER_LABELS, "river type")}


def dashboard_rows(dashboard_id, flop_types=(), turn_types=(), river_types=(), faced_sizes=(), date_from=None,
                   date_to=None):
    board = dashboard(dashboard_id)
    filters = check_filters(flop_types, turn_types, river_types, faced_sizes)
    rows = []
    for entry in board["lines"]:
        spec = parse_line(entry["line"], board["role"], board["position"])
        street = spec.decision.street
        row = {**entry, "street": street, "measured": list(spec.measured),
               "reason": blank_reason(street, turn_types, river_types),
               "size_filter_ignored": bool(faced_sizes) and not splits_by_size(spec),
               "user": None, "gto": None, "gap": {}}
        if row["reason"] is None:
            row["user"] = side(side_matches(user_matches(board, entry["line"], date_from, date_to), spec, filters,
                                            faced_sizes), spec)
            row["gto"] = side(side_matches(gto_matches(board, entry["line"]), spec, filters, faced_sizes), spec)
            row["gap"] = gap(row["user"], row["gto"])
        rows.append(row)
    return rows
