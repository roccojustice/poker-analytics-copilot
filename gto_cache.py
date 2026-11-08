"""The GTO side of the dashboards, computed once: each line's matches, classified, stored in cache/."""
import os
import re
import threading
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

from db import gto_engine, gto_hero_id, run_spot_query
from line_parser import parse_line
from spot_sql import build_spot_query
from spotlight import classify

CACHE_DIR = Path("cache")
CHUNK = 50_000
_loaded = {}  # path -> frame, so a request never re-reads a pickle
_locks = {}  # path -> lock, so concurrent requests build a line once
_locks_guard = threading.Lock()


def cache_key():
    """Names the cache after the GTO DB, its hand count and last id: a re-import never serves stale numbers."""
    engine = gto_engine()
    stats = pd.read_sql("SELECT count(*) AS n, max(id_hand) AS last FROM cash_hand_summary", engine).iloc[0]
    return f"{engine.url.database}-{int(stats['n'])}-{int(stats['last'])}"


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
    if path in _loaded:
        return _loaded[path]
    with _locks_guard:
        lock = _locks.setdefault(path, threading.Lock())
    with lock:
        if path not in _loaded:
            _loaded[path] = pd.read_pickle(path) if path.exists() else _build(path, pot, position, role, line, formations)
    return _loaded[path]


def _build(path, pot, position, role, line, formations):
    spec = parse_line(line, role, position)
    where, params, measured_sql = build_spot_query(pot, position, role, spec, formations)
    matches = run_spot_query(where, params, measured_sql, id_player=gto_hero_id(), engine=gto_engine())
    matches = _classify(matches, spec.decision.street)
    matches = matches.astype({c: "category" for c in matches.columns if matches[c].dtype == object})
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".partial")
    try:
        matches.to_pickle(partial)
        os.replace(partial, path)  # atomic: a reader sees the old file or the whole new one
    finally:
        partial.unlink(missing_ok=True)
    return matches


def build():
    """Builds every dashboard line's cache, printing hand counts and times."""
    import time
    from dashboards import DASHBOARDS
    for board in DASHBOARDS.values():
        for entry in board["lines"]:
            start = time.time()
            matches = line_matches(board["pot"], board["position"], board["role"], entry["line"], board["formations"])
            print(f"{entry['name']:<20} {len(matches):>10,} hands  {time.time() - start:6.1f} s", flush=True)


if __name__ == "__main__":
    import sys
    if sys.argv[1:] != ["build"]:
        sys.exit("usage: python gto_cache.py build")
    build()
