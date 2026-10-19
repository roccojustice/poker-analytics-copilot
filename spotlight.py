import pandas as pd

from db import run_spot_query, get_hand_details
from line_parser import parse_line, STREET_NAMES
from sizing import SIZE_BUCKETS, size_text
from spot_sql import build_spot_query, splits_by_size

ACTION_NAMES = {"B": "Bet", "X": "Check", "F": "Fold", "C": "Call", "R": "Raise"}


def _street_text(spec_street, actors, tail=()):
    size = [f"bet {size_text(spec_street.size)}"] if spec_street.size else []
    return f"{STREET_NAMES[spec_street.street].capitalize()}: " + ", ".join(actors + size + list(tail))


def describe(pot, position, role, formations, spec, n_hands, date_from=None, date_to=None):
    parts = [pot.upper(), position.upper(), role.upper(), ", ".join(formations) or "Any"]
    if date_from and date_to:
        parts.append(f"{date_from} → {date_to}")
    elif date_from:
        parts.append(f"from {date_from}")
    elif date_to:
        parts.append(f"until {date_to}")
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


def run_spot(pot, position, role, line, formations=(), date_from=None, date_to=None):
    pot, position, role = pot.lower(), position.lower(), role.lower()
    formations = list(dict.fromkeys(formations))
    spec = parse_line(line, role, position)
    where, params, measured_sql = build_spot_query(pot, position, role, spec, formations, date_from, date_to)
    matches = run_spot_query(where, params, measured_sql)
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
        "interpreted_filter": describe(pot, position, role, formations, spec, len(matches), date_from, date_to),
        "distribution": _distribution(unsized, spec.measured, prefix),
        "split": _split(labels, prefix) if split else None,
        "hands": hands,
    }
