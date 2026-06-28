from analytics import (
    winrate_by_position,
    winrate_by_site,
    threebet_by_position,
)


def run_query(query_name, df):
    if query_name == "winrate_position":
        return winrate_by_position(df)

    elif query_name == "winrate_site":
        return winrate_by_site(df)

    elif query_name == "threebet_position":
        return threebet_by_position(df)

    else:
        raise ValueError(f"Unknown query: {query_name}")