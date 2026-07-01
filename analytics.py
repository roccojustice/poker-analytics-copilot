
def analyze_metric(df, group_by, metric):
    df = df.copy()
    if metric not in METRIC_CONFIGS:
        raise ValueError(f"Unknown metric: {metric}")

    config = METRIC_CONFIGS[metric]
    if "generate_columns" in config:
        for col_name, func in config["generate_columns"].items():
            df[col_name] = func(df)

    result = df.groupby(group_by).agg(hands=(group_by, "count"), **config["agg"])

    if config["derived"]:
        for col_name, func in config["derived"].items():
            result[col_name] = func(result)

    return result.sort_values(config["sort_by"], ascending=False)

METRIC_CONFIGS = {
    "winrate": {
        "generate_columns": {
            "bb_won": lambda df: df["amt_won"] / df["amt_bb"],
        },
        "derived": {
            "bb_per_100": lambda result: result["avg_bb_per_hand"] * 100
        },
        "agg": {
            "bb_won": ("bb_won", "sum"),
            "avg_bb_per_hand": ("bb_won", "mean")
        },
        "sort_by": "bb_per_100",
    },
    "threebet": {
        "derived": {
            "threebet_pct": lambda result: result["threebets"] / result["opportunities"] * 100
        },
        "agg": {
            "opportunities": ("flg_p_3bet_opp", "sum"),
            "threebets": ("flg_p_3bet", "sum")
        },
        "sort_by": "threebet_pct",
    },
    "preflop_stats": {
        "derived": {
            "vpip_pct": lambda result: result["vpip_hands"] / result["hands"] * 100,
            "pfr_pct": lambda result: result["pfr_hands"] / result["hands"] * 100
        },
        "agg": {
            "pfr_hands": ("pfr", "sum"),
            "vpip_hands": ("vpip", "sum"),
        },
        "sort_by": "vpip_pct",
    }
}


def analyze_metric(df, group_by, metric):
    df = df.copy()
    if metric not in METRIC_CONFIGS:
        raise ValueError(f"Unknown metric: {metric}")

    config = METRIC_CONFIGS[metric]
    if "generate_columns" in config:
        for col_name, func in config["generate_columns"].items():
            df[col_name] = func(df)

    result = df.groupby(group_by).agg(hands=(group_by, "count"), **config["agg"])

    if config["derived"]:
        for col_name, func in config["derived"].items():
            result[col_name] = func(result)

    return result.sort_values(config["sort_by"], ascending=False)
