from analytics import (
    analyze_metric,
    METRIC_CONFIGS,
    get_hero_df,
    since_date_filter,
)
from db import (
    FILTER_QUERIES,
    run_filter_query,
    get_hand_details,
)

from queries import AVAILABLE_QUERIES

def run_query(query_name, group_by=None, limit=None, since_date=None):
    if query_name in METRIC_CONFIGS:
        if limit is not None:
            raise ValueError(f"Limit is not applicable for metric queries: {query_name}")
        if group_by not in AVAILABLE_QUERIES[query_name]["group_by_options"]:
            raise ValueError(f"Invalid group by option for {query_name}: {group_by}")
        df = get_hero_df()
        if since_date is not None:
            df = since_date_filter(df, since_date)
        return analyze_metric(df, group_by, query_name)
    if query_name in FILTER_QUERIES:
        if group_by is not None:
            raise ValueError(f"Group by is not applicable for filter queries: {query_name}")
        matching_hands = run_filter_query(query_name, limit=limit, since_date=since_date)
        return get_hand_details(matching_hands["id_hand"])
    raise ValueError(f"Unknown query: {query_name}")

def is_filter_query(query_name):
    return query_name in FILTER_QUERIES