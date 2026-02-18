"""Tests for P6 StorageBackend, RedisCache, and PostgresStorage interfaces."""

import json
import pytest
from unittest.mock import MagicMock, patch

from stellar_memory.config import StorageConfig
from stellar_memory.models import MemoryItem
from stellar_memory.storage import StorageBackend
from stellar_memory.storage.redis_cache import RedisCache


# ---------- StorageBackend ABC ----------

class DummyBackend(StorageBackend):
    """Concrete stub for testing the ABC."""
    def __init__(self):
        self._data = {}
        self._connected = False

    def connect(self):
        self._connected = True

    def disconnect(self):
        self._connected = False

    def is_connected(self):
        return self._connected

    def store(self, item):
        self._data[item.id] = item

    def get(self, item_id):
        return self._data.get(item_id)

    def remove(self, item_id):
        return self._data.pop(item_id, None) is not None

    def update(self, item):
        self._data[item.id] = item

    def search(self, query, limit=5, query_embedding=None, zone=None):
        results = []
        for item in self._data.values():
            if zone is not None and item.zone != zone:
                continue
            if query.lower() in item.content.lower():
                results.append(item)
        return results[:limit]

    def get_all(self, zone=None):
        if zone is not None:
            return [i for i in self._data.values() if i.zone == zone]
        return list(self._data.values())

    def count(self, zone=None):
        return len(self.get_all(zone))

    def get_lowest_score_item(self, zone):
        items = self.get_all(zone)
        return min(items, key=lambda x: x.total_score) if items else None


def _make_item(content="test", zone=0, score=0.5):
    item = MemoryItem.create(content, 0.5)
    item.zone = zone
    item.total_score = score
    return item


class TestStorageBackendABC:
    def test_concrete_impl_works(self):
        backend = DummyBackend()
        backend.connect()
        assert backend.is_connected()

        item = _make_item("hello")
        backend.store(item)
        assert backend.get(item.id) is item
        assert backend.count() == 1
        assert backend.count(zone=0) == 1
        assert backend.count(zone=1) == 0

    def test_search_with_zone(self):
        backend = DummyBackend()
        backend.store(_make_item("alpha", zone=0))
        backend.store(_make_item("beta", zone=1))
        assert len(backend.search("alpha", zone=0)) == 1
        assert len(backend.search("alpha", zone=1)) == 0

    def test_remove(self):
        backend = DummyBackend()
        item = _make_item("bye")
        backend.store(item)
        assert backend.remove(item.id)
        assert backend.get(item.id) is None
        assert not backend.remove("nonexistent")

    def test_get_lowest_score(self):
        backend = DummyBackend()
        backend.store(_make_item("low", zone=0, score=0.1))
        backend.store(_make_item("high", zone=0, score=0.9))
        lowest = backend.get_lowest_score_item(0)
        assert lowest.total_score == 0.1

    def test_health_check(self):
        backend = DummyBackend()
        assert not backend.health_check()
        backend.connect()
        assert backend.health_check()

    def test_disconnect(self):
        backend = DummyBackend()
        backend.connect()
        backend.disconnect()
        assert not backend.is_connected()


# ---------- RedisCache ----------

class TestRedisCache:
    def test_init_defaults(self):
        cache = RedisCache("redis://localhost:6379", ttl=60)
        assert not cache.is_connected()
        assert cache.get("nonexistent") is None

    def test_set_skips_uncached_zones(self):
        cache = RedisCache("redis://localhost", cached_zones=(0, 1))
        cache._client = MagicMock()
        cache._connected = True
        item = _make_item("outer", zone=3)
        cache.set(item)  # should be skipped
        cache._client.setex.assert_not_called()

    def test_set_caches_zone_0(self):
        cache = RedisCache("redis://localhost", ttl=120)
        cache._client = MagicMock()
        cache._connected = True
        item = _make_item("core", zone=0)
        cache.set(item)
        cache._client.setex.assert_called_once()
        args = cache._client.setex.call_args
        assert args[0][0] == f"sm:{item.id}"
        assert args[0][1] == 120

    def test_get_returns_none_when_no_client(self):
        cache = RedisCache("redis://localhost")
        assert cache.get("any") is None

    def test_invalidate(self):
        cache = RedisCache("redis://localhost")
        cache._client = MagicMock()
        cache._connected = True
        cache.invalidate("item-1")
        cache._client.delete.assert_called_once_with("sm:item-1")

    def test_serialize_deserialize(self):
        cache = RedisCache("redis://localhost")
        item = _make_item("roundtrip", zone=1)
        item.encrypted = True
        item.source_type = "web"
        data = cache._serialize(item)
        restored = cache._deserialize(data)
        assert restored.id == item.id
        assert restored.content == item.content
        assert restored.zone == 1
        assert restored.encrypted is True
        assert restored.source_type == "web"

    def test_connect_import_error(self):
        cache = RedisCache("redis://localhost")
        with patch.dict("sys.modules", {"redis": None}):
            with pytest.raises(ImportError):
                cache.connect()


# ---------- StorageConfig ----------

class TestStorageConfig:
    def test_defaults(self):
        cfg = StorageConfig()
        assert cfg.backend == "sqlite"
        assert cfg.db_url is None
        assert cfg.pool_size == 10
        assert cfg.redis_url is None

    def test_custom(self):
        cfg = StorageConfig(
            backend="postgresql",
            db_url="postgresql://localhost/test",
            redis_url="redis://localhost",
        )
        assert cfg.backend == "postgresql"
        assert cfg.db_url == "postgresql://localhost/test"


# ---------- PostgresStorage (interface only, no real connection) ----------

class TestPostgresStorageInterface:
    def test_import(self):
        from stellar_memory.storage.postgres_storage import PostgresStorage
        pg = PostgresStorage("postgresql://localhost/test")
        assert not pg.is_connected()

    def test_health_check_not_connected(self):
        from stellar_memory.storage.postgres_storage import PostgresStorage
        pg = PostgresStorage("postgresql://localhost/test")
        assert not pg.health_check()
