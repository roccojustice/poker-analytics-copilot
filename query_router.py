from analytics import (
    winrate_by,
    threebet_by_position,
)

def run_query(query_name, df, group_by=None):
    if query_name == "threebet_position":
        return threebet_by_position(df)
    
    elif query_name == "winrate":
        return winrate_by(df, group_by)
    
    else:
        raise ValueError(f"Unknown query: {query_name}")
    