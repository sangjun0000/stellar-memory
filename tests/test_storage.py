"""Tests for storage implementations - InMemoryStorage and SqliteStorage."""

import os
import tempfile
import time

from stellar_memory.models import MemoryItem
from stellar_memory.storage.in_memory import InMemoryStorage
from stellar_memory.storage.sqlite_storage import SqliteStorage


def make_item(id: str = "m1", content: str = "test memory", **kwargs) -> MemoryItem:
    defaults = dict(
        created_at=time.time(), last_recalled_at=time.time(),
        recall_count=0, arbitrary_importance=0.5, zone=0, metadata={},
        total_score=0.5,
    )
    defaults.update(kwargs)
    return MemoryItem(id=id, content=content, **defaults)


class TestInMemoryCRUD:
    def test_store_and_get(self):
        storage = InMemoryStorage()
        item = make_item("m1", "hello world")
        storage.store(item)
        result = storage.get("m1")
        assert result is not None
        assert result.content == "hello world"

    def test_get_nonexistent(self):
        storage = InMemoryStorage()
        assert storage.get("missing") is None

    def test_remove(self):
        storage = InMemoryStorage()
        storage.store(make_item("m1"))
        assert storage.remove("m1") is True
        assert storage.get("m1") is None

    def test_remove_nonexistent(self):
        storage = InMemoryStorage()
        assert storage.remove("missing") is False

    def test_update(self):
        storage = InMemoryStorage()
        item = make_item("m1", "original")
        storage.store(item)
        item.content = "updated"
        item.recall_count = 5
        storage.update(item)
        result = storage.get("m1")
        assert result.content == "updated"
        assert result.recall_count == 5

    def test_get_all(self):
        storage = InMemoryStorage()
        for i in range(5):
            storage.store(make_item(f"m{i}"))
        assert len(storage.get_all()) == 5

    def test_count(self):
        storage = InMemoryStorage()
        assert storage.count() == 0
        storage.store(make_item("m1"))
        assert storage.count() == 1

    def test_get_lowest_score_item(self):
        storage = InMemoryStorage()
        storage.store(make_item("m1", total_score=0.9))
        storage.store(make_item("m2", total_score=0.1))
        storage.store(make_item("m3", total_score=0.5))
        lowest = storage.get_lowest_score_item()
        assert lowest.id == "m2"

    def test_get_lowest_score_empty(self):
        storage = InMemoryStorage()
        assert storage.get_lowest_score_item() is None


class TestInMemorySearch:
    def test_search_single_keyword(self):
        storage = InMemoryStorage()
        storage.store(make_item("m1", "python programming"))
        storage.store(make_item("m2", "java programming"))
        storage.store(make_item("m3", "cooking recipe"))
        results = storage.search("python")
        assert len(results) == 1
        assert results[0].id == "m1"

    def test_search_multiple_keywords(self):
        storage = InMemoryStorage()
        storage.store(make_item("m1", "important meeting tomorrow"))
        storage.store(make_item("m2", "meeting notes"))
        results = storage.search("meeting tomorrow")
        assert len(results) >= 1
        assert results[0].id == "m1"  # Higher match score

    def test_search_no_match(self):
        storage = InMemoryStorage()
        storage.store(make_item("m1", "hello world"))
        results = storage.search("quantum")
        assert len(results) == 0

    def test_search_respects_limit(self):
        storage = InMemoryStorage()
        for i in range(10):
            storage.store(make_item(f"m{i}", f"common word item {i}"))
        results = storage.search("common", limit=3)
        assert len(results) == 3


class TestSqliteCRUD:
    def _make_storage(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self._db_path = path
        self._storage = SqliteStorage(path, zone_id=2)
        return self._storage

    def teardown_method(self):
        if hasattr(self, "_storage") and hasattr(self._storage, "_local"):
            conn = getattr(self._storage._local, "conn", None)
            if conn:
                conn.close()
                self._storage._local.conn = None
        if hasattr(self, "_db_path"):
            for suffix in ["", "-wal", "-shm"]:
                p = self._db_path + suffix
                if os.path.exists(p):
                    try:
                        os.unlink(p)
                    except PermissionError:
                        pass

    def test_store_and_get(self):
        storage = self._make_storage()
        item = make_item("m1", "hello sqlite", zone=2)
        storage.store(item)
        result = storage.get("m1")
        assert result is not None
        assert result.content == "hello sqlite"

    def test_get_nonexistent(self):
        storage = self._make_storage()
        assert storage.get("missing") is None

    def test_remove(self):
        storage = self._make_storage()
        storage.store(make_item("m1", zone=2))
        assert storage.remove("m1") is True
        assert storage.get("m1") is None

    def test_remove_nonexistent(self):
        storage = self._make_storage()
        assert storage.remove("missing") is False

    def test_update(self):
        storage = self._make_storage()
        item = make_item("m1", "original", zone=2)
        storage.store(item)
        item.recall_count = 10
        item.total_score = 0.8
        storage.update(item)
        result = storage.get("m1")
        assert result.recall_count == 10
        assert result.total_score == 0.8

    def test_upsert(self):
        storage = self._make_storage()
        item = make_item("m1", "version 1", zone=2)
        storage.store(item)
        item.content = "version 2"
        storage.store(item)  # INSERT OR REPLACE
        assert storage.count() == 1
        assert storage.get("m1").content == "version 2"

    def test_count(self):
        storage = self._make_storage()
        assert storage.count() == 0
        storage.store(make_item("m1", zone=2))
        storage.store(make_item("m2", zone=2))
        assert storage.count() == 2

    def test_get_all(self):
        storage = self._make_storage()
        for i in range(5):
            storage.store(make_item(f"m{i}", f"item {i}", zone=2))
        assert len(storage.get_all()) == 5

    def test_get_lowest_score_item(self):
        storage = self._make_storage()
        storage.store(make_item("m1", total_score=0.9, zone=2))
        storage.store(make_item("m2", total_score=0.1, zone=2))
        lowest = storage.get_lowest_score_item()
        assert lowest.id == "m2"

    def test_search_keyword(self):
        storage = self._make_storage()
        storage.store(make_item("m1", "python programming", zone=2))
        storage.store(make_item("m2", "cooking recipe", zone=2))
        results = storage.search("python")
        assert len(results) >= 1
        assert results[0].content == "python programming"

    def test_metadata_json_roundtrip(self):
        storage = self._make_storage()
        item = make_item("m1", zone=2, metadata={"tag": "important", "score": 42})
        storage.store(item)
        result = storage.get("m1")
        assert result.metadata == {"tag": "important", "score": 42}
