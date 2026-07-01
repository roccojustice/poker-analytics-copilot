import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

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