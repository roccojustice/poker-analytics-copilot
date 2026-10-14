from filter_recipes import assemble_where
from line_parser import SpotInputError

# Preflop part of the validated recipes (SCHEMA_NOTES.md); position is added separately.
PREFLOP_CONTEXTS = {
    ("2bp", "pfr"): ["first_raise", "no_limpers_faced", "no_face_raise_preflop"],
    ("3bp", "pfr"): [
        "made_3bet", "had_3bet_opp", ("own_raises", "=", 1), "faced_raise_preflop",
        "no_4bet_faced", "no_squeeze_made",
    ],
    ("2bp", "pfc"): [
        "vpip", "no_first_raise", "no_3bet_made", ("own_raises", "=", 0),
        "faced_raise_preflop", "no_fold_preflop", "no_3bet_def_faced",
    ],
    ("3bp", "pfc"): [
        ("own_raises", "<=", 1), "faced_3bet_preflop", "no_4bet_made", "no_4bet_faced",
        "no_fold_preflop", "no_squeeze_def_faced", "first_raise", "no_limpers_faced",
    ],
}
POSITION_ATOMS = {"ip": "ip_flop", "oop": "oop_flop"}

SEATS = {"SB": 9, "BB": 8, "UTG": 3, "MP": 2, "CO": 1, "BTN": 0}
POSTFLOP_ORDER = ["SB", "BB", "UTG", "MP", "CO", "BTN"]
FORMATIONS = [
    f"{oop} vs {ip}"
    for i, oop in enumerate(POSTFLOP_ORDER)
    for ip in POSTFLOP_ORDER[i + 1:]
]


def build_spot_query(pot, position, role, spec, formations=()):
    if pot not in ("2bp", "3bp"):
        raise SpotInputError(f"Unknown pot: {pot}")
    items = PREFLOP_CONTEXTS[(pot, role)] + ["heads_up_flop", POSITION_ATOMS[position]]
    where, params = assemble_where(items)

    for s in spec.completed:
        where += f" AND h_{s.street}.action = %(h_{s.street})s"
        where += f" AND v_{s.street}.action = %(v_{s.street})s"
        params[f"h_{s.street}"] = s.hero
        params[f"v_{s.street}"] = s.villain

    d = spec.decision
    measured_sql = f"substr(h_{d.street}.action, %(measure_pos)s, 1)"
    where += f" AND h_{d.street}.action LIKE %(h_{d.street}_prefix)s"
    where += f" AND v_{d.street}.action LIKE %(v_{d.street}_prefix)s"
    where += f" AND {measured_sql} = ANY(%(measured)s)"
    params[f"h_{d.street}_prefix"] = d.hero + "%"
    params[f"v_{d.street}_prefix"] = d.villain + "%"
    params["measure_pos"] = len(d.hero) + 1
    params["measured"] = list(spec.measured)

    selected = list(dict.fromkeys(formations))  # dedupe, keep order
    unknown = [f for f in selected if f not in FORMATIONS]
    if unknown:
        raise SpotInputError(f"Unknown formation: {unknown[0]}")
    if selected:
        pairs = []
        for i, formation in enumerate(selected):
            oop_seat, ip_seat = formation.split(" vs ")
            hero_seat, villain_seat = (oop_seat, ip_seat) if position == "oop" else (ip_seat, oop_seat)
            pairs.append(f"(%(hero_pos_{i})s, %(villain_pos_{i})s)")
            params[f"hero_pos_{i}"] = SEATS[hero_seat]
            params[f"villain_pos_{i}"] = SEATS[villain_seat]
        where += f" AND (chps.position, v.position) IN ({', '.join(pairs)})"

    return where, params, measured_sql
