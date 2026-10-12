import pandas as pd

from db import run_spot_query, get_hand_details
from line_parser import parse_line, STREET_NAMES
from spot_sql import build_spot_query

ACTION_NAMES = {"B": "Bet", "X": "Check", "F": "Fold", "C": "Call", "R": "Raise"}


def describe(pot, position, role, formation, spec, n_hands):
    parts = [pot.upper(), position.upper(), role.upper(), formation or "Any"]
    for s in spec.completed:
        parts.append(f"{STREET_NAMES[s.street].capitalize()}: Hero {s.hero}, villain {s.villain}")
    d = spec.decision
    seen = [f"Hero {d.hero}"] * bool(d.hero) + [f"villain {d.villain}"] * bool(d.villain)
    measuring = "measuring " + " / ".join(spec.measured)
    parts.append(f"{STREET_NAMES[d.street].capitalize()}: " + ", ".join(seen + [measuring]))
    parts.append(f"{n_hands:,} hands")
    return " · ".join(parts)


def _distribution(measured_actions, measured):
    counts = measured_actions.value_counts()
    total = int(counts.sum())
    return [
        {
            "action": action,
            "name": ACTION_NAMES[action],
            "hands": int(counts.get(action, 0)),
            "pct": round(counts.get(action, 0) / total * 100, 1) if total else 0.0,
        }
        for action in measured
    ]


def run_spot(pot, position, role, line, formation=None):
    spec = parse_line(line, role, position)
    where, params, measured_sql = build_spot_query(pot, position, role, spec, formation)
    matches = run_spot_query(where, params, measured_sql)

    if matches.empty:
        hands = pd.DataFrame()  # nothing to render, skip the detail round-trip
    else:
        hands = get_hand_details(matches["id_hand"]).merge(matches, on="id_hand", how="left")
        hands = hands.astype(object).where(hands.notna(), None)

    return {
        "interpreted_filter": describe(pot, position, role, formation, spec, len(matches)),
        "distribution": _distribution(matches["measured_action"], spec.measured),
        "hands": hands,
    }
