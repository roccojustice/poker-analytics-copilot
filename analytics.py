def winrate_by(df, group_by):
    df = df.copy()
    df["BB Won"] = df["amt_won"] / df["amt_bb"]
    result = (
        df.groupby(group_by)
        .agg(
            hands=(group_by, "count"),
            bb_won=("BB Won", "sum"),
            avg_bb_per_hand=("BB Won", "mean")
        )
    )
    result["bb_per_100"] = result["avg_bb_per_hand"] * 100
    return result.sort_values("bb_per_100", ascending=False)

def threebet(df, group_by):
    result = (
        df.groupby(group_by)
        .agg(
            opportunities=("flg_p_3bet_opp", "sum"),
            threebets=("flg_p_3bet", "sum")
        )
    )
    result["threebet_pct"] = result["threebets"] / result["opportunities"] * 100
    return result.sort_values("threebet_pct", ascending=False)