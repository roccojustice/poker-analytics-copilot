"""The GTO side of the dashboards, computed once: each line's matches, classified, stored in cache/."""
import re
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

from db import gto_engine, gto_hero_id, run_spot_query
from line_parser import parse_line
from spot_sql import build_spot_query
from spotlight import classify

CACHE_DIR = Path("cache")
CHUNK = 50_000


def cache_key():
    """Names the cache after the GTO DB and its hand count, so a re-import never serves stale numbers."""
    engine = gto_engine()
    count = int(pd.read_sql("SELECT count(*) AS n FROM cash_hand_summary", engine)["n"].iloc[0])
    return f"{engine.url.database}-{count}"


def _slug(pot, position, role, line, formations):
    return re.sub(r"[^A-Za-z0-9+-]", "_", "_".join([pot, position, role, line, "+".join(formations)]))


def _classify_chunk(args):
    chunk, street = args
    return classify(chunk, street)


def _classify(matches, street):
    if len(matches) <= CHUNK:
        return classify(matches, street)
    chunks = [(matches.iloc[i:i + CHUNK], street) for i in range(0, len(matches), CHUNK)]
    with Pool() as pool:
        return pd.concat(pool.map(_classify_chunk, chunks))


def line_matches(pot, position, role, line, formations):
    """The GTO bot's hands for a Line: id_hand, measured_action and the classification columns."""
    path = CACHE_DIR / cache_key() / f"{_slug(pot, position, role, line, formations)}.pkl"
    if path.exists():
        return pd.read_pickle(path)
    spec = parse_line(line, role, position)
    where, params, measured_sql = build_spot_query(pot, position, role, spec, formations)
    matches = run_spot_query(where, params, measured_sql, id_player=gto_hero_id(), engine=gto_engine())
    matches = _classify(matches, spec.decision.street)
    matches = matches.astype({c: "category" for c in matches.columns if matches[c].dtype == object})
    path.parent.mkdir(parents=True, exist_ok=True)
    matches.to_pickle(path)
    return matches
