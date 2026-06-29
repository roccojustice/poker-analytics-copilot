from analytics import (
    winrate_by,
    threebet,
)

def run_query(query_name, df, group_by=None):
    if query_name == "threebet":
        return threebet(df, group_by)
    
    elif query_name == "winrate":
        return winrate_by(df, group_by)
    
    else:
        raise ValueError(f"Unknown query: {query_name}")
    