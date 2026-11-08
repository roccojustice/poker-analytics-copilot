from pathlib import Path

import pandas as pd
import pytest

import gto_cache
import spotlight
from test_spotlight import fake_matches


@pytest.fixture
def fake_db(monkeypatch, tmp_path):
    calls = []
    rows = fake_matches([(1, "Bs"), (2, "X"), (3, "Bl", "AhKh2c")])

    def fake_query(where, params, measured_sql, id_player=None, engine=None):
        calls.append(id_player)
        return rows.copy()

    monkeypatch.setattr("gto_cache.run_spot_query", fake_query)
    monkeypatch.setattr("gto_cache.gto_hero_id", lambda: 99)
    monkeypatch.setattr("gto_cache.gto_engine", lambda: None)
    monkeypatch.setattr("gto_cache.cache_key", lambda: "gto-3")
    monkeypatch.setattr("gto_cache.CACHE_DIR", tmp_path)
    return calls, rows, tmp_path


def test_miss_queries_classifies_and_stores(fake_db):
    calls, _, cache_dir = fake_db
    out = gto_cache.line_matches("2bp", "ip", "pfr", "X", ["BB vs BTN"])
    assert calls == [99]
    assert len(list((cache_dir / "gto-3").glob("*.pkl"))) == 1
    assert list(out["id_hand"]) == [1, 2, 3]


def test_hit_does_not_query(fake_db):
    calls, _, _ = fake_db
    gto_cache.line_matches("2bp", "ip", "pfr", "X", ["BB vs BTN"])
    gto_cache.line_matches("2bp", "ip", "pfr", "X", ["BB vs BTN"])
    assert len(calls) == 1


def test_new_key_rebuilds(fake_db, monkeypatch):
    calls, _, cache_dir = fake_db
    gto_cache.line_matches("2bp", "ip", "pfr", "X", ["BB vs BTN"])
    monkeypatch.setattr("gto_cache.cache_key", lambda: "gto-4")
    gto_cache.line_matches("2bp", "ip", "pfr", "X", ["BB vs BTN"])
    assert len(calls) == 2
    assert (cache_dir / "gto-4").is_dir()


def test_classification_matches_spotlight(fake_db):
    _, rows, _ = fake_db
    out = gto_cache.line_matches("2bp", "ip", "pfr", "X", ["BB vs BTN"])
    expected = spotlight.classify(rows, "f")
    for column in ["measured_action", "flop_type", "hand_type", "draw_type"]:
        assert list(out[column].astype(object)) == list(expected[column])


def test_chunked_classification_equals_single_pass(fake_db, monkeypatch):
    _, rows, _ = fake_db
    monkeypatch.setattr("gto_cache.CHUNK", 1)
    chunked = gto_cache._classify(rows, "f")
    pd.testing.assert_frame_equal(chunked, spotlight.classify(rows, "f"))


def test_loaded_lines_stay_in_memory(fake_db, monkeypatch):
    gto_cache.line_matches("2bp", "ip", "pfr", "X", ["BB vs BTN"])
    gto_cache._loaded.clear()
    reads = []
    real = pd.read_pickle
    monkeypatch.setattr("gto_cache.pd.read_pickle", lambda path: reads.append(path) or real(path))
    gto_cache.line_matches("2bp", "ip", "pfr", "X", ["BB vs BTN"])
    gto_cache.line_matches("2bp", "ip", "pfr", "X", ["BB vs BTN"])
    assert len(reads) == 1


def test_cache_key_changes_when_ids_change_at_equal_count(monkeypatch):
    class FakeEngine:
        class url:
            database = "gto"
    monkeypatch.setattr("gto_cache.gto_engine", lambda: FakeEngine)
    stats = {"n": 1500, "last": 1500}
    monkeypatch.setattr("gto_cache.pd.read_sql", lambda q, e: pd.DataFrame([stats]))
    first = gto_cache.cache_key()
    stats["last"] = 3000  # regenerated: same count, new ids
    assert gto_cache.cache_key() != first


def test_failed_write_leaves_no_pickle(fake_db, monkeypatch):
    _, _, cache_dir = fake_db

    def broken(self, path, *args, **kwargs):
        Path(path).write_bytes(b"half")
        raise OSError("disk full")

    monkeypatch.setattr(pd.DataFrame, "to_pickle", broken)
    with pytest.raises(OSError):
        gto_cache.line_matches("2bp", "ip", "pfr", "X", ["BB vs BTN"])
    assert list((cache_dir / "gto-3").glob("*.pkl")) == []


def test_concurrent_requests_build_a_line_once(fake_db, monkeypatch):
    import threading
    import time
    calls, rows, _ = fake_db

    def slow_query(where, params, measured_sql, id_player=None, engine=None):
        calls.append(id_player)
        time.sleep(0.2)
        return rows.copy()

    monkeypatch.setattr("gto_cache.run_spot_query", slow_query)
    threads = [threading.Thread(target=gto_cache.line_matches, args=("2bp", "ip", "pfr", "X", ["BB vs BTN"]))
               for _ in range(3)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert len(calls) == 1
