import pandas as pd

from board_types import FLOP_TYPES, RIVER_LABELS, TURN_LABELS, flop_type, river_labels, turn_labels
from db import run_spot_query, get_hand_details
from draws import DRAW_TYPES, draw_type
from hand_strength import HAND_GROUPS, HAND_TYPES, hand_type
from line_parser import parse_line, STREET_NAMES, SpotInputError
from sizing import SIZE_BUCKETS, size_text
from spot_sql import build_spot_query, splits_by_size

ACTION_NAMES = {"B": "Bet", "X": "Check", "F": "Fold", "C": "Call", "R": "Raise"}


def _street_text(spec_street, actors, tail=()):
    size = [f"bet {size_text(spec_street.size)}"] if spec_street.size else []
    return f"{STREET_NAMES[spec_street.street].capitalize()}: " + ", ".join(actors + size + list(tail))


def describe(pot, position, role, formations, spec, n_hands, date_from=None, date_to=None, flop_types=(),
             turn_types=(), river_types=(), hand_types=(), draw_types=()):
    parts = [pot.upper(), position.upper(), role.upper(), ", ".join(formations) or "Any"]
    if date_from and date_to:
        parts.append(f"{date_from} → {date_to}")
    elif date_from:
        parts.append(f"from {date_from}")
    elif date_to:
        parts.append(f"until {date_to}")
    if flop_types:
        parts.append("Flop type: " + ", ".join(flop_types))
    if turn_types:
        parts.append("Turn type: " + ", ".join(turn_types))
    if river_types:
        parts.append("River type: " + ", ".join(river_types))
    if hand_types:
        parts.append("Hand: " + ", ".join(hand_types))
    if draw_types:
        parts.append("Draw: " + ", ".join(draw_types))
    for s in spec.completed:
        parts.append(_street_text(s, [f"Hero {s.hero}", f"villain {s.villain}"]))
    d = spec.decision
    seen = [f"Hero {d.hero}"] * bool(d.hero) + [f"villain {d.villain}"] * bool(d.villain)
    measuring = "measuring " + " / ".join(d.hero + action for action in spec.measured)
    parts.append(_street_text(d, seen, [measuring]))
    parts.append(f"{n_hands:,} hands")
    return " · ".join(parts)


def _row(action, label, name, hands, total, parent=None):
    row = {"action": action, "label": label, "name": name, "hands": hands, "pct": _pct(hands, total)}
    if parent:
        row["parent"] = parent
    return row


def _distribution(labels, measured, prefix):
    counts = labels.value_counts()
    total = int(counts.sum())
    rows = []
    for action in measured:
        label = prefix + action
        if action != "B":
            rows.append(_row(action, label, ACTION_NAMES[action], int(counts.get(label, 0)), total))
            continue
        subs = [(f"B{k.lower()}", f"Bet {name}") for k, (name, _, _) in SIZE_BUCKETS.items()]
        sub_counts = [int(counts.get(prefix + sub, 0)) for sub, _ in subs]
        rows.append(_row("B", label, "Bet", sum(sub_counts), total))
        rows += [_row(sub, prefix + sub, name, n, total, parent=label)
                 for (sub, name), n in zip(subs, sub_counts)]
    return rows


def _pct(part, whole):
    return round(part / whole * 100, 1) if whole else 0.0


def _split(labels, prefix):
    counts = labels.value_counts()
    rows = []
    for key, (name, _, _) in SIZE_BUCKETS.items():
        cells = [{"action": action, "label": prefix + action + key.lower(),
                  "hands": int(counts.get(prefix + action + key.lower(), 0))} for action in ("F", "C", "R")]
        row_hands = sum(cell["hands"] for cell in cells)
        for cell in cells:
            cell["pct"] = _pct(cell["hands"], row_hands)
        rows.append({"size": key, "name": name, "hands": row_hands,
                     "pct_faced": _pct(row_hands, len(labels)), "cells": cells})
    return rows


def _type_row(key, name, mask, labels, spec, prefix):
    return {key: name, "hands": int(mask.sum()), "pct_total": _pct(int(mask.sum()), len(mask)),
            "cells": _distribution(labels[mask], spec.measured, prefix)}


def _hand_split(types, labels, spec, prefix):
    group_of = {leaf: group for group, leaves in HAND_GROUPS.items() for leaf in leaves}

    def row(name, members):
        return _type_row("hand_type", name, types.isin(members), labels, spec, prefix)

    rows = []
    for t in HAND_TYPES:
        if not (types == t).any():
            continue
        group = group_of.get(t)
        if group and not any(r["hand_type"] == group for r in rows):
            rows.append(row(group, HAND_GROUPS[group]))  # the group row sits before its first leaf
        rows.append(row(t, [t]) | ({"parent": group} if group else {}))
    return rows


def _draw_split(types, labels, spec, prefix):
    return [_type_row("draw_type", t, types == t, labels, spec, prefix) for t in DRAW_TYPES if (types == t).any()]


def _board_column(matches, cards, label):
    return pd.Series([label(*row) for row in matches[cards].itertuples(index=False)], index=matches.index, dtype=object)


def _labels_column(matches, cards, labeler):
    return _board_column(matches, cards, lambda *ids: ", ".join(labeler(*ids)))


def _keep(column, selected):
    return column.map(lambda labels: bool(set(labels.split(", ")) & set(selected)))


def _with_board_types(matches, street, flop_types, turn_types, river_types):
    cards = ["card_1", "card_2", "card_3", "card_4", "card_5"]
    none = pd.Series(None, index=matches.index, dtype=object)
    matches = matches.assign(
        flop_type=_board_column(matches, cards[:3], flop_type),
        turn_type=_labels_column(matches, cards[:4], turn_labels) if street in ("t", "r") else none,
        river_type=_labels_column(matches, cards, river_labels) if street == "r" else none,
    )
    keep = pd.Series(True, index=matches.index)
    if flop_types:
        keep &= matches["flop_type"].isin(flop_types)
    if turn_types:
        keep &= _keep(matches["turn_type"], turn_types)
    if river_types:
        keep &= _keep(matches["river_type"], river_types)
    return matches[keep]


BOARD_SIZE = {"f": 3, "t": 4, "r": 5}


def _with_hand_and_draw(matches, street, hand_types, draw_types):
    cards = ["holecard_1", "holecard_2", *[f"card_{i}" for i in range(1, BOARD_SIZE[street] + 1)]]  # decision street
    matches = matches.assign(hand_type=_board_column(matches, cards, hand_type),
                             draw_type=_board_column(matches, cards, draw_type))
    if hand_types:
        matches = matches[matches["hand_type"].isin(hand_types)]
    if draw_types:
        matches = matches[matches["draw_type"].isin(draw_types)]
    return matches.drop(columns=["holecard_1", "holecard_2", "card_1", "card_2", "card_3", "card_4", "card_5"])


def _checked(values, registry, name):
    values = list(dict.fromkeys(values))
    unknown = [v for v in values if v not in registry]
    if unknown:
        raise SpotInputError(f"Unknown {name}: {unknown[0]}")
    return values


def run_spot(pot, position, role, line, formations=(), date_from=None, date_to=None, flop_types=(),
             turn_types=(), river_types=(), hand_types=(), draw_types=()):
    pot, position, role = pot.lower(), position.lower(), role.lower()
    formations = list(dict.fromkeys(formations))
    flop_types = _checked(flop_types, FLOP_TYPES, "flop type")
    turn_types = _checked(turn_types, TURN_LABELS, "turn type")
    river_types = _checked(river_types, RIVER_LABELS, "river type")
    hand_types = _checked(hand_types, HAND_TYPES, "hand type")
    draw_types = _checked(draw_types, DRAW_TYPES, "draw type")
    spec = parse_line(line, role, position)
    street = spec.decision.street
    if turn_types and street == "f":
        raise SpotInputError("Turn type needs a decision on the turn or river")
    if river_types and street != "r":
        raise SpotInputError("River type needs a decision on the river")
    where, params, measured_sql = build_spot_query(pot, position, role, spec, formations, date_from, date_to)
    matches = run_spot_query(where, params, measured_sql)
    matches = _with_board_types(matches, street, flop_types, turn_types, river_types)
    matches = _with_hand_and_draw(matches, street, hand_types, draw_types)
    prefix = spec.decision.hero
    matches = matches.assign(measured_action=prefix + matches["measured_action"])  # letter -> label
    split = splits_by_size(spec)
    labels = matches["measured_action"]
    unsized = labels.str[:len(prefix) + 1] if split else labels  # XCs -> XC for the 1D rows

    if matches.empty:
        hands = pd.DataFrame()  # nothing to render, skip the detail round-trip
    else:
        hands = get_hand_details(matches["id_hand"]).merge(matches, on="id_hand", how="left")
        hands = hands.astype(object).where(hands.notna(), None)

    return {
        "interpreted_filter": describe(pot, position, role, formations, spec, len(matches), date_from, date_to, flop_types,
                                       turn_types, river_types, hand_types, draw_types),
        "distribution": _distribution(unsized, spec.measured, prefix),
        "split": _split(labels, prefix) if split else None,
        "hand_split": _hand_split(matches["hand_type"], unsized, spec, prefix),
        "draw_split": _draw_split(matches["draw_type"], unsized, spec, prefix),
        "hands": hands,
    }
