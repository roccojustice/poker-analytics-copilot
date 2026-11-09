"""GTO dashboards: per spot, the user's frequencies next to the GTO bot DB's, line by line."""
import time

import pandas as pd

import board_groups
from board_types import FLOP_TYPES, RIVER_LABELS, TURN_LABELS
from db import get_hand_details, gto_engine, gto_hero_id, run_spot_query
from gto_cache import line_matches
from line_parser import SpotInputError, parse_line
from sizing import SIZE_BUCKETS
from spot_sql import build_spot_query, splits_by_size
from draws import DRAW_TYPES
from hand_strength import HAND_TYPES
from spotlight import _checked, _distribution, _draw_split, _hand_split, _split, classify, filter_types

GTO_HANDS_SHOWN = 200
USER_CACHE_SECONDS = 600  # new imports show up within 10 min
_user_cache = {}

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
    """The user's hands for a Line from the user DB, classified like the GTO side; reused for 10 min."""
    key = (board["name"], line, date_from, date_to)
    stamp, matches = _user_cache.get(key, (None, None))
    if stamp is None or time.monotonic() - stamp > USER_CACHE_SECONDS:
        matches = _query_user(board, line, date_from, date_to)
        _user_cache[key] = (time.monotonic(), matches)
    return matches


def _query_user(board, line, date_from, date_to):
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


def group_pick(dashboard_id, board_group):
    """A board_group request field -> (group, negate), or None for Any."""
    if not board_group:
        return None
    return board_groups.find(dashboard_id, board_group["name"]), bool(board_group.get("negate"))


def groups(dashboard_id):
    dashboard(dashboard_id)
    return board_groups.load(dashboard_id)


def save_groups(dashboard_id, new_groups):
    dashboard(dashboard_id)
    return board_groups.save(dashboard_id, new_groups)


def side_matches(matches, spec, filters, faced_sizes, group=None):
    """Applies the type filters, the board group and, on a response to a bet, the faced-size filter."""
    matches = filter_types(matches, **filters)
    if group:
        keep = board_groups.in_group(matches, group[0])
        matches = matches[~keep if group[1] else keep]
    if faced_sizes and splits_by_size(spec):
        size_letters = [s.lower() for s in faced_sizes]
        matches = matches[matches["measured_action"].astype(str).str[-1].isin(size_letters)]
    return matches


def labels(matches, spec):
    """measured_action -> the hands page's labels: decision prefix + letter (+ size letter on bets)."""
    prefix = spec.decision.hero
    full = prefix + matches["measured_action"].astype(str)
    return full, (full.str[:len(prefix) + 1] if splits_by_size(spec) else full)


def _no_data(rows, hands):
    """No hands means no frequency: pct None, not 0.0%."""
    return [dict(r, pct=None) for r in rows] if not hands else rows


def _split_rows(full, prefix):
    return [dict(r, cells=_no_data(r["cells"], r["hands"])) for r in _split(full, prefix)]


def side(matches, spec):
    _, unsized = labels(matches, spec)
    return {"hands": len(matches),
            "distribution": _no_data(_distribution(unsized, spec.measured, spec.decision.hero), len(matches))}


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
                   date_to=None, board_group=None):
    board = dashboard(dashboard_id)
    filters = check_filters(flop_types, turn_types, river_types, faced_sizes)
    group = group_pick(dashboard_id, board_group)
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
                                            faced_sizes, group), spec)
            row["gto"] = side(side_matches(gto_matches(board, entry["line"]), spec, filters, faced_sizes, group),
                              spec)
            row["gap"] = gap(row["user"], row["gto"])
        rows.append(row)
    return rows


def line_entry(board, line_id):
    entry = next((e for e in board["lines"] if e["id"] == line_id), None)
    if entry is None:
        raise SpotInputError(f"Unknown line: {line_id}")
    return entry


def hand_rows(matches, full, fetch):
    """Hand details merged with the label and the type columns; NaN -> None for JSON."""
    if matches.empty:
        return []
    extra = matches.assign(measured_action=full).astype(object)
    hands = fetch(list(matches["id_hand"])).merge(extra, on="id_hand", how="left")
    return hands.astype(object).where(hands.notna(), None).to_dict(orient="records")


def action_labels(spec):
    """Every pickable label of a line's action tables -> the labels it selects (an overall B selects its sizes)."""
    prefix = spec.decision.hero
    rows = _distribution(pd.Series([], dtype=object), spec.measured, prefix)
    picks = {r["label"]: {r["label"]} for r in rows}
    for r in rows:
        if r.get("parent"):
            picks[r["parent"]].add(r["label"])
    if splits_by_size(spec):
        picks.update({c["label"]: {c["label"]} for row in _split(pd.Series([], dtype=object), prefix)
                      for c in row["cells"]})
    return picks


def filter_actions(matches, spec, actions):
    if not actions:
        return matches
    picks = action_labels(spec)
    selected = set().union(*(picks[a] for a in actions))
    full, unsized = labels(matches, spec)
    return matches[full.isin(selected) | unsized.isin(selected)]


def detail(matches, spec, hand_types, draw_types, fetch, shown=None, actions=()):
    """One side of a line's detail; each table counts over the other tables' picks only."""
    prefix = spec.decision.hero
    by_types = filter_types(matches, hand_types=hand_types, draw_types=draw_types)
    by_action = filter_actions(matches, spec, actions)
    by_draw = filter_types(by_action, draw_types=draw_types)
    by_hand = filter_types(by_action, hand_types=hand_types)
    picked = filter_types(by_draw, hand_types=hand_types)
    full, unsized = labels(by_types, spec)
    shown_hands = picked.sort_values("id_hand").head(shown) if shown else picked
    return {
        "hands_total": len(picked),
        "distribution": _no_data(_distribution(unsized, spec.measured, prefix), len(by_types)),
        "split": _split_rows(full, prefix) if splits_by_size(spec) else None,
        "hand_split": _hand_split(by_draw["hand_type"].astype(object), labels(by_draw, spec)[1], spec, prefix),
        "draw_split": _draw_split(by_hand["draw_type"].astype(object), labels(by_hand, spec)[1], spec, prefix),
        "hands": hand_rows(shown_hands, labels(shown_hands, spec)[0], fetch),
    }


def line_detail(dashboard_id, line_id, flop_types=(), turn_types=(), river_types=(), faced_sizes=(), hand_types=(),
                draw_types=(), date_from=None, date_to=None, actions=(), board_group=None):
    board = dashboard(dashboard_id)
    entry = line_entry(board, line_id)
    filters = check_filters(flop_types, turn_types, river_types, faced_sizes)
    hand_types = _checked(hand_types, HAND_TYPES, "hand type")
    draw_types = _checked(draw_types, DRAW_TYPES, "draw type")
    spec = parse_line(entry["line"], board["role"], board["position"])
    actions = _checked(actions, action_labels(spec), "action")
    reason = blank_reason(spec.decision.street, turn_types, river_types)
    if reason:
        raise SpotInputError(reason)
    group = group_pick(dashboard_id, board_group)
    user = side_matches(user_matches(board, entry["line"], date_from, date_to), spec, filters, faced_sizes, group)
    gto = side_matches(gto_matches(board, entry["line"]), spec, filters, faced_sizes, group)
    return {
        "line": entry,
        "user": detail(user, spec, hand_types, draw_types, get_hand_details, actions=actions),
        "gto": detail(gto, spec, hand_types, draw_types,
                      lambda ids: get_hand_details(ids, id_player=gto_hero_id(), engine=gto_engine()),
                      shown=GTO_HANDS_SHOWN, actions=actions),
    }
