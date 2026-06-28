def winrate_by_position(df):
    result = (
        df.groupby("Position")
        .agg(
            hands=("Position", "count"),
            bb_won=("BB Won", "sum"),
            avg_bb_per_hand=("BB Won", "mean")
        )
    )
    result["bb_per_100"] = result["avg_bb_per_hand"] * 100
    return result.sort_values("bb_per_100", ascending=False)


def winrate_by_site(df):
    result = (
        df.groupby("Site")
        .agg(
            hands=("Site", "count"),
            bb_won=("BB Won", "sum"),
            avg_bb_per_hand=("BB Won", "mean")
        )
    )
    result["bb_per_100"] = result["avg_bb_per_hand"] * 100
    return result.sort_values("bb_per_100", ascending=False)


def threebet_by_position(df):
    opps = df[df["Facing PF Action"] == "1 Raiser"].copy()
    opps["is_3bet"] = opps["PF Act"].astype(str).str.startswith("R")

    result = (
        opps.groupby("Position")
        .agg(
            opportunities=("is_3bet", "count"),
            threebets=("is_3bet", "sum")
        )
    )
    result["threebet_pct"] = result["threebets"] / result["opportunities"] * 100
    return result.sort_values("threebet_pct", ascending=False)