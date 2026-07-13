import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from poker_cards import decode_card_id

load_dotenv()

def get_hero_hands():
    engine = create_engine(f'postgresql+psycopg2://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}')

    query = """
        SELECT amt_won, cl.amt_bb, flg_p_3bet_opp, flg_p_3bet, description AS position, site_name AS site, flg_vpip AS vpip, flg_p_first_raise AS pfr
        FROM cash_hand_player_statistics chps
        JOIN 
            (SELECT DISTINCT ON (position) position, description
            FROM lookup_positions) lp ON chps.position = lp.position
        JOIN
            cash_limit cl ON chps.id_limit = cl.id_limit
        JOIN
            cash_hand_summary chs ON chps.id_hand = chs.id_hand
        JOIN
            lookup_sites ls ON chs.id_site = ls.id_site
        WHERE chps.id_player IN (10, 9580)"""

    df = pd.read_sql(query, engine)
    engine.dispose()
    return df

def hand_filter_fold_to_3bet_preflop(id_player=10, limit=None):
    engine = create_engine(f'postgresql+psycopg2://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}')

    query = """
        WITH hand_raise_totals AS (
            SELECT id_hand, SUM(cnt_p_raise) AS total_p_raises
            FROM cash_hand_player_statistics
            GROUP BY id_hand
        )
        SELECT chps.id_hand
        FROM cash_hand_player_statistics chps
            JOIN hand_raise_totals hrt ON chps.id_hand = hrt.id_hand
            JOIN cash_hand_summary chs ON chps.id_hand = chs.id_hand
        WHERE chps.id_player = %(id_player)s
            AND chps.flg_p_first_raise = true
            AND chps.flg_p_face_raise = true
            AND chps.flg_p_4bet_def_opp = false
            AND chps.flg_p_fold = true
            AND hrt.total_p_raises >= 2
            AND chps.cnt_p_face_limpers = 0
        ORDER BY chps.id_hand"""

    params = {"id_player": id_player}
    if limit is not None:
        query += " LIMIT %(limit)s"
        params["limit"] = limit

    df = pd.read_sql(query, engine, params=params)
    engine.dispose()
    return df


def hand_filter_fold_vs_small_cbet_2bp_oop_pfc(id_player=10, limit=None):
    engine = create_engine(f'postgresql+psycopg2://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}')

    query = """
        WITH hand_raise_totals AS (
            SELECT id_hand, SUM(cnt_p_raise) AS total_p_raises
            FROM cash_hand_player_statistics
            GROUP BY id_hand
        )
        SELECT chps.id_hand
        FROM cash_hand_player_statistics chps
        JOIN hand_raise_totals hrt ON chps.id_hand = hrt.id_hand
        JOIN cash_hand_summary chs ON chps.id_hand = chs.id_hand
        WHERE chps.id_player = %(id_player)s
          AND chps.flg_p_first_raise = false
          AND hrt.total_p_raises = 1
          AND chs.cnt_players_f = 2
          AND chps.flg_f_has_position = false
          AND chps.flg_f_cbet_def_opp = true
          AND chps.val_f_bet_facing_pct BETWEEN 20 AND 33
          AND chps.flg_f_check_raise = false
          AND chps.flg_f_fold = true
        ORDER BY chps.id_hand"""

    params = {"id_player": id_player}
    if limit is not None:
        query += " LIMIT %(limit)s"
        params["limit"] = limit

    df = pd.read_sql(query, engine, params=params)
    engine.dispose()
    return df


def hand_filter_check_river_2bp_ip_pfr(id_player=10, limit=None):
    engine = create_engine(f'postgresql+psycopg2://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}')

    query = """
        WITH hand_raise_totals AS (
            SELECT id_hand, SUM(cnt_p_raise) AS total_p_raises
            FROM cash_hand_player_statistics
            GROUP BY id_hand
        )
        SELECT chps.id_hand
        FROM cash_hand_player_statistics chps
        JOIN hand_raise_totals hrt ON chps.id_hand = hrt.id_hand
        JOIN cash_hand_summary chs ON chps.id_hand = chs.id_hand
        WHERE chps.id_player = %(id_player)s
          AND chps.flg_p_first_raise = true
          AND hrt.total_p_raises = 1
          AND chps.cnt_p_face_limpers = 0
          AND chps.flg_r_has_position = true
          AND chps.flg_r_check = true
          AND chs.cnt_players_f = 2
          AND chs.cnt_players_r = 2
        ORDER BY chps.id_hand"""

    params = {"id_player": id_player}
    if limit is not None:
        query += " LIMIT %(limit)s"
        params["limit"] = limit

    df = pd.read_sql(query, engine, params=params)
    engine.dispose()
    return df

def get_hand_details(id_hands, id_player=10):
    engine = create_engine(f'postgresql+psycopg2://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}')

    query = """
        SELECT
            chps.id_hand,
            chps.date_played,
            lp.description AS position,
            hr_final.group_name AS final_hand_group,
            hr_final.group_details AS final_hand_details,
            chps.holecard_1,
            chps.holecard_2,
            chs.card_1, chs.card_2, chs.card_3, chs.card_4, chs.card_5,
            la_f.action AS f_act,
            la_t.action AS t_act,
            la_r.action AS r_act,
            chps.amt_bet_f,
            chps.amt_bet_t,
            chps.amt_bet_r,
            chs.amt_pot,
            cl.amt_bb,
            chps.amt_won,
            p.player_name AS winner,
            hr_win.group_name AS winning_hand_group,
            hr_win.group_details AS winning_hand_details
        FROM cash_hand_player_statistics chps
        JOIN
            (SELECT DISTINCT ON (position) position, description
            FROM lookup_positions) lp ON chps.position = lp.position
        JOIN
            cash_limit cl ON chps.id_limit = cl.id_limit
        JOIN
            cash_hand_summary chs ON chps.id_hand = chs.id_hand
        LEFT JOIN
            lookup_hand_ranks hr_final ON chps.id_final_hand = hr_final.id_hand_rank
        LEFT JOIN
            lookup_hand_ranks hr_win ON chs.id_win_hand = hr_win.id_hand_rank
        LEFT JOIN
            lookup_actions la_f ON chps.id_action_f = la_f.id_action
        LEFT JOIN
            lookup_actions la_t ON chps.id_action_t = la_t.id_action
        LEFT JOIN
            lookup_actions la_r ON chps.id_action_r = la_r.id_action
        LEFT JOIN
            player p ON chs.id_winner = p.id_player
        WHERE chps.id_hand = ANY(%(id_hands)s)
          AND chps.id_player = %(id_player)s
        ORDER BY chps.date_played"""

    params = {"id_hands": list(id_hands), "id_player": id_player}
    df = pd.read_sql(query, engine, params=params)
    engine.dispose()

    def decode(card_id):
        if pd.isna(card_id) or card_id == 0:
            return None
        rank, suit = decode_card_id(int(card_id))
        return f"{rank}{suit}"

    df["hole_cards"] = df["holecard_1"].apply(decode) + " " + df["holecard_2"].apply(decode)
    df["flop"] = df[["card_1", "card_2", "card_3"]].apply(
        lambda row: " ".join(filter(None, (decode(c) for c in row))), axis=1
    )
    df["turn"] = df["card_4"].apply(decode)
    df["river"] = df["card_5"].apply(decode)
    df["final_hand"] = df["final_hand_group"] + ", " + df["final_hand_details"]
    df["winning_hand"] = df["winning_hand_group"] + ", " + df["winning_hand_details"]

    df = df.drop(columns=[
        "holecard_1", "holecard_2", "card_1", "card_2", "card_3", "card_4", "card_5",
        "final_hand_group", "final_hand_details", "winning_hand_group", "winning_hand_details",
    ])

    df = df.fillna({
        "final_hand": "No showdown",
        "winning_hand": "No showdown",
        "flop": "",
        "turn": "",
        "river": "",
        "f_act": "",
        "t_act": "",
        "r_act": "",
    })

    return df


FILTER_QUERIES = {
    "check_river_2bp_ip_pfr": hand_filter_check_river_2bp_ip_pfr,
    "fold_to_3bet_preflop": hand_filter_fold_to_3bet_preflop,
    "fold_vs_small_cbet_2bp_oop_pfc": hand_filter_fold_vs_small_cbet_2bp_oop_pfc,
}


def run_filter_query(filter_name, limit=None, id_player=10):
    if filter_name not in FILTER_QUERIES:
        raise ValueError(f"Unknown filter: {filter_name}")
    return FILTER_QUERIES[filter_name](id_player=id_player, limit=limit)