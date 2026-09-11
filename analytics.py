import pandas as pd
from db import get_hero_hands, run_distribution_query
from hero_responses import get_hero_response


_cached_df = None


def since_date_filter(df, since_date):
    df = df[df["date_played"] >= pd.to_datetime(since_date)]
    return df

def get_hero_df():
    global _cached_df
    if _cached_df is None:
        _cached_df = get_hero_hands()
    return _cached_df


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


def compute_distribution(where_clause, params, hero_response_name, id_player=10, since_date=None):
    hero_response = get_hero_response(hero_response_name)
    counts_df = run_distribution_query(
        where_clause,
        params,
        hero_response["flag_column"],
        hero_response["actions"],
        id_player=id_player,
        since_date=since_date,
    )

    counts = counts_df.iloc[0].to_dict()
    total = sum(counts.values())
    return {
        action_name: {"count": count, "pct": count / total * 100}
        for action_name, count in counts.items()
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

    if "derived" in config:
        for col_name, func in config["derived"].items():
            result[col_name] = func(result)

    return result.sort_values(config["sort_by"], ascending=False)
