"""Diff a Spotlight result against a PT4 hand-list export by hand_no, both directions."""
import argparse
import re

import pandas as pd

from db import engine
from sizing import SIZE_BUCKETS
from spotlight import run_spot


def normalize_hand_no(value):
    text = str(value).strip()
    if re.fullmatch(r"\d+(\.\d+)?[eE][+-]?\d+", text):
        raise ValueError(f"hand_no {text!r} is in scientific notation; re-export with full numbers")
    return text[:-2] if text.endswith(".0") else text


def diff_hand_sets(spot, export):
    return {"extra": spot - export, "missing": export - spot}


def filter_by_label(hands, label):
    if label is None or hands.empty:
        return hands
    labels = {label} | {label + k.lower() for k in SIZE_BUCKETS}  # an overall B row keeps its sizes
    return hands[hands["measured_action"].isin(labels)]


def export_hand_nos(csv_path, column):
    df = pd.read_csv(csv_path, dtype=str)
    return {normalize_hand_no(v) for v in df[column].dropna()}


def spot_hand_nos(id_hands):
    if not id_hands:
        return set()
    df = pd.read_sql(
        "SELECT hand_no FROM cash_hand_summary WHERE id_hand = ANY(%(ids)s)",
        engine,
        params={"ids": id_hands},
    )
    return {normalize_hand_no(v) for v in df["hand_no"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv")
    parser.add_argument("pot")
    parser.add_argument("position")
    parser.add_argument("role")
    parser.add_argument("line")
    parser.add_argument("--formation", action="append", default=[])
    parser.add_argument("--column", default="Hand #")
    parser.add_argument("--label")
    args = parser.parse_args()

    result = run_spot(args.pot, args.position, args.role, args.line, args.formation)
    hands = filter_by_label(result["hands"], args.label)
    spot = spot_hand_nos([] if hands.empty else [int(i) for i in hands["id_hand"]])
    export = export_hand_nos(args.csv, args.column)
    diff = diff_hand_sets(spot, export)

    print(result["interpreted_filter"])
    print(f"Spotlight {len(spot)} · PT4 {len(export)} · extra {len(diff['extra'])} · missing {len(diff['missing'])}")
    for side in ("extra", "missing"):
        if diff[side]:
            print(f"{side}: {sorted(diff[side])[:20]}")


if __name__ == "__main__":
    main()
