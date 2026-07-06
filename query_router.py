from analytics import (
    analyze_metric,
    METRIC_CONFIGS,
    get_hero_df,
)
from db import (
    FILTER_QUERIES,
    run_filter_query,
    get_hand_details,
)

def run_query(query_name, group_by=None, limit=None):
    if query_name in METRIC_CONFIGS:
        df = get_hero_df()
        return analyze_metric(df, group_by, query_name)
    if query_name in FILTER_QUERIES:
        matching_hands = run_filter_query(query_name, limit=limit)
        return get_hand_details(matching_hands["id_hand"])
    raise ValueError(f"Unknown query: {query_name}")

def is_filter_query(query_name):
    return query_name in FILTER_QUERIES