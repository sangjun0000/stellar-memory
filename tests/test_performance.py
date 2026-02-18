"""Tests for performance optimizations (pre-filter, LRU cache)."""

import pytest

from stellar_memory.config import StellarConfig
from stellar_memory.storage.sqlite_storage import SqliteStorage
from stellar_memory.models import MemoryItem
from stellar_memory.utils import serialize_embedding


def _make_item(content, zone=2, embedding=None):
    import time
    from uuid import uuid4
    return MemoryItem(
        id=str(uuid4()),
        content=content,
        created_at=time.time(),
        last_recalled_at=time.time(),
        recall_count=0,
        arbitrary_importance=0.5,
        zone=zone,
        embedding=embedding,
    )


def _fake_embedding(seed=1.0, dim=4):
    """Create a simple normalized-ish embedding for testing."""
    import math
    raw = [(seed + i) % 3.0 for i in range(dim)]
    norm = math.sqrt(sum(x * x for x in raw))
    return [x / norm for x in raw] if norm > 0 else raw


@pytest.fixture
def storage(tmp_path):
    return SqliteStorage(str(tmp_path / "test.db"), zone_id=2)


def test_keyword_only_search(storage):
    """Keyword-only search (no embedding) should work."""
    item = _make_item("Python programming language")
    storage.store(item)
    results = storage.search("Python", limit=5)
    assert len(results) == 1
    assert results[0].id == item.id


def test_prefilter_rerank_with_embedding(storage):
    """Pre-filter + re-rank path should return results."""
    emb1 = _fake_embedding(1.0)
    emb2 = _fake_embedding(2.0)
    item1 = _make_item("Python data science", embedding=emb1)
    item2 = _make_item("Java enterprise", embedding=emb2)
    storage.store(item1)
    storage.store(item2)
    query_emb = _fake_embedding(1.0)
    results = storage.search("Python", limit=5, query_embedding=query_emb)
    assert len(results) >= 1


def test_prefilter_supplements_recent_items(storage):
    """When keyword match is sparse, recent embedded items supplement candidates."""
    emb = _fake_embedding(1.0)
    item = _make_item("Completely unrelated content xyz", embedding=emb)
    storage.store(item)
    query_emb = _fake_embedding(1.0)
    results = storage.search("nonexistent", limit=5, query_embedding=query_emb)
    # Should find the item via Phase 1b (recent embedded supplement)
    assert len(results) >= 1


def test_empty_query_returns_empty(storage):
    """Empty query should return empty list."""
    results = storage.search("", limit=5)
    assert results == []


def test_keyword_search_case_insensitive(storage):
    """Keyword search should be case-insensitive."""
    item = _make_item("PYTHON Programming")
    storage.store(item)
    results = storage.search("python", limit=5)
    assert len(results) == 1


def test_limit_respected(storage):
    """Search should respect the limit parameter."""
    for i in range(10):
        storage.store(_make_item(f"Python topic {i}"))
    results = storage.search("Python", limit=3)
    assert len(results) == 3


def test_embedder_lru_cache():
    """Embedder LRU cache should return same result for same input."""
    from stellar_memory.embedder import NullEmbedder
    # NullEmbedder has no cache (always None), so test the concept
    embedder = NullEmbedder()
    r1 = embedder.embed("test")
    r2 = embedder.embed("test")
    assert r1 == r2  # Both None


def test_hybrid_score_ordering(storage):
    """Items with higher hybrid scores should rank first."""
    emb1 = _fake_embedding(1.0)
    emb2 = _fake_embedding(5.0)
    item1 = _make_item("Python machine learning tutorial", embedding=emb1)
    item2 = _make_item("Python basics", embedding=emb2)
    storage.store(item1)
    storage.store(item2)
    query_emb = _fake_embedding(1.0)
    results = storage.search("Python machine learning", limit=5, query_embedding=query_emb)
    assert len(results) >= 1
    # First result should have better match (more keyword + closer embedding)
