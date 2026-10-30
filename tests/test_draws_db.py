from collections import Counter

import pandas as pd
import pytest
from sqlalchemy import text

from board_types import RANKS
from db import engine
from draws import _straight, draw_parts
from poker_cards import decode_card_id
from spotlight import run_spot

pytestmark = pytest.mark.db

BOARD = {"f": 3, "t": 4}
NUT_FLUSH_DRAW = {10, 20}  # PT4 flush draw strength: one-card / two-card nut (SCHEMA_NOTES, Session 67)


def load(street):
    board = [f"card_{i}" for i in range(1, BOARD[street] + 1)]
    backdoor = ", c.flg_f_bflush_draw AS bflush" if street == "f" else ""
    query = text(f"""
        SELECT chps.id_hand, chps.holecard_1, chps.holecard_2, {", ".join("chs." + c for c in board)},
               c.flg_{street}_flush_draw AS fd, c.id_{street}_flush_draw_strength AS fd_strength,
               c.flg_{street}_straight_draw AS sd, c.flg_{street}_2gutshot_draw AS gut2,
               c.flg_{street}_gutshot_draw AS gut{backdoor}
        FROM cash_hand_player_statistics chps
            JOIN cash_hand_summary chs ON chs.id_hand = chps.id_hand
            JOIN cash_hand_player_combinations c ON c.id_hand = chps.id_hand AND c.id_player = chps.id_player
        WHERE chps.id_player = 10 AND chps.flg_{street}_saw""")
    df = pd.read_sql(query, engine)
    rows = []
    for r in df[["holecard_1", "holecard_2", *board]].itertuples(index=False):
        hole, cards = [decode_card_id(int(c)) for c in r[:2]], [decode_card_id(int(c)) for c in r[2:]]
        rows.append((*draw_parts(hole, cards), *definitions_differ(hole, cards)))
    df[["o_fd", "o_nut", "o_outs", "o_bd", "board_suit", "made_flush", "board_straight"]] = pd.DataFrame(
        rows, index=df.index)
    return df


def definitions_differ(hole, board):
    """Where PT4 counts a draw GTO Wizard doesn't: a board-only suit, a made flush, a board-only straight."""
    on_board = Counter(suit for _, suit in board)
    in_hole = Counter(suit for _, suit in hole)
    board_suit = any(n >= 3 and not in_hole[suit] for suit, n in on_board.items())
    made_flush = max((on_board + in_hole).values()) >= 5
    board_straight = any(_straight(board + [(rank, "x")]) for rank in RANKS)
    return board_suit, made_flush, board_straight


@pytest.fixture(scope="module", params=["f", "t"])
def street_rows(request):
    return request.param, load(request.param)


def mismatches(rows, ours, pt4):
    bad = rows[ours != pt4]
    return f"{len(bad)} of {len(rows)} disagree:\n" + bad.head(30).to_string()


def test_flush_draw_matches_pt4(street_rows):
    street, rows = street_rows
    rows = rows[~rows["board_suit"]]  # PT4 counts a four-flush board Hero holds none of
    assert (rows["o_fd"] == rows["fd"]).all(), mismatches(rows, rows["o_fd"], rows["fd"])


def test_nut_flush_draw_matches_pt4(street_rows):
    street, rows = street_rows
    rows = rows[rows["o_fd"]]
    nut = rows["fd_strength"].isin(NUT_FLUSH_DRAW)
    assert (rows["o_nut"] == nut).all(), mismatches(rows, rows["o_nut"], nut)


def test_straight_draws_match_pt4(street_rows):
    street, rows = street_rows
    rows = rows[~rows["made_flush"] & ~rows["board_straight"]]  # PT4 clears draws under a flush, counts board ones
    pt4 = pd.Series(0, index=rows.index).mask(rows["gut"], 1).mask(rows["sd"] | rows["gut2"], 2)
    if street == "t":  # PT4 calls some turn double gutshots a gutshot (SCHEMA_NOTES, Session 67)
        pt4 = pt4.mask((rows["o_outs"] == 2) & rows["gut"], 2)
    assert (rows["o_outs"] == pt4).all(), mismatches(rows, rows["o_outs"], pt4)


def test_backdoor_matches_pt4():
    rows = load("f")
    rows = rows[~rows["board_suit"]]  # PT4 calls a monotone flop a backdoor for every hand
    ours = rows["o_bd"] > 0
    assert (ours == rows["bflush"]).all(), mismatches(rows, ours, rows["bflush"])


SPOTS = [("2bp", "oop", "pfc", "vs B?"), ("2bp", "ip", "pfr", "- B-?"), ("2bp", "ip", "pfr", "- B-B-?")]


@pytest.mark.parametrize("spot", SPOTS, ids=lambda spot: spot[3])
def test_draw_split_rows_sum_to_hand_count(spot):
    result = run_spot(*spot)
    assert sum(row["hands"] for row in result["draw_split"]) == len(result["hands"])
    if spot[3] == "- B-B-?":
        assert [row["draw_type"] for row in result["draw_split"]] == ["No draw"]
