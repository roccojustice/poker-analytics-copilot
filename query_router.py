from analytics import (
    analyze_metric
)

def run_query(query_name, df, group_by=None):   
    return analyze_metric(df, group_by, query_name)

    