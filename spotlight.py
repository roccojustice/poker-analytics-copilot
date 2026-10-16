import pandas as pd

from db import run_spot_query, get_hand_details
from line_parser import parse_line, STREET_NAMES
from spot_sql import build_spot_query

ACTION_NAMES = {"B": "Bet", "X": "Check", "F": "Fold", "C": "Call", "R": "Raise"}


def describe(pot, position, role, formations, spec, n_hands, date_from=None, date_to=None):
    parts = [pot.upper(), position.upper(), role.upper(), ", ".join(formations) or "Any"]
    if date_from and date_to:
        parts.append(f"{date_from} → {date_to}")
    elif date_from:
        parts.append(f"from {date_from}")
    elif date_to:
        parts.append(f"until {date_to}")
    for s in spec.completed:
        parts.append(f"{STREET_NAMES[s.street].capitalize()}: Hero {s.hero}, villain {s.villain}")
    d = spec.decision
    seen = [f"Hero {d.hero}"] * bool(d.hero) + [f"villain {d.villain}"] * bool(d.villain)
    measuring = "measuring " + " / ".join(d.hero + action for action in spec.measured)
    parts.append(f"{STREET_NAMES[d.street].capitalize()}: " + ", ".join(seen + [measuring]))
    parts.append(f"{n_hands:,} hands")
    return " · ".join(parts)


def _distribution(labels, measured, prefix):
    counts = labels.value_counts()
    total = int(counts.sum())
    rows = []
    for action in measured:
        label = prefix + action
        hands = int(counts.get(label, 0))
        rows.append({
            "action": action,
            "label": label,
            "name": ACTION_NAMES[action],
            "hands": hands,
            "pct": round(hands / total * 100, 1) if total else 0.0,
        })
    return rows


def run_spot(pot, position, role, line, formations=(), date_from=None, date_to=None):
    pot, position, role = pot.lower(), position.lower(), role.lower()
    formations = list(dict.fromkeys(formations))
    spec = parse_line(line, role, position)
    where, params, measured_sql = build_spot_query(pot, position, role, spec, formations, date_from, date_to)
    matches = run_spot_query(where, params, measured_sql)
    prefix = spec.decision.hero
    matches = matches.assign(measured_action=prefix + matches["measured_action"])  # letter -> label

    if matches.empty:
        hands = pd.DataFrame()  # nothing to render, skip the detail round-trip
    else:
        hands = get_hand_details(matches["id_hand"]).merge(matches, on="id_hand", how="left")
        hands = hands.astype(object).where(hands.notna(), None)

    return {
        "interpreted_filter": describe(pot, position, role, formations, spec, len(matches), date_from, date_to),
        "distribution": _distribution(matches["measured_action"], spec.measured, prefix),
        "hands": hands,
    }
