"""Tests for export/import serialization and snapshots."""

import json
import math
import time
import pytest
from uuid import uuid4

from stellar_memory.config import StellarConfig
from stellar_memory.models import MemoryItem, MemorySnapshot
from stellar_memory.serializer import MemorySerializer
from stellar_memory.stellar import StellarMemory


def _fake_embedding(seed=1.0, dim=4):
    raw = [(seed + i) % 3.0 for i in range(dim)]
    norm = math.sqrt(sum(x * x for x in raw))
    return [x / norm for x in raw] if norm > 0 else raw


def _make_item(content, zone=1, embedding=None):
    now = time.time()
    return MemoryItem(
        id=str(uuid4()),
        content=content,
        created_at=now,
        last_recalled_at=now,
        recall_count=2,
        arbitrary_importance=0.7,
        zone=zone,
        metadata={"key": "value"},
        embedding=embedding,
        total_score=0.65,
    )


@pytest.fixture
def serializer():
    return MemorySerializer(embedder_dim=4)


def test_export_json(serializer):
    """export_json should produce valid JSON."""
    items = [_make_item("Test content")]
    result = serializer.export_json(items)
    data = json.loads(result)
    assert data["version"] == "0.3.0"
    assert data["count"] == 1
    assert len(data["items"]) == 1


def test_import_json(serializer):
    """import_json should restore MemoryItems."""
    items = [_make_item("Imported content")]
    json_str = serializer.export_json(items)
    restored = serializer.import_json(json_str)
    assert len(restored) == 1
    assert restored[0].content == "Imported content"
    assert restored[0].recall_count == 2
    assert restored[0].arbitrary_importance == 0.7


def test_roundtrip_data_integrity(serializer):
    """export -> import should preserve all fields."""
    emb = _fake_embedding(1.0)
    item = _make_item("Round trip test", zone=2, embedding=emb)
    json_str = serializer.export_json([item])
    restored = serializer.import_json(json_str)
    r = restored[0]
    assert r.id == item.id
    assert r.content == item.content
    assert r.zone == item.zone
    assert r.total_score == item.total_score
    assert r.metadata == item.metadata


def test_embedding_base64_roundtrip(serializer):
    """Embedding should survive base64 encode/decode."""
    emb = _fake_embedding(3.14)
    item = _make_item("With embedding", embedding=emb)
    json_str = serializer.export_json([item])
    restored = serializer.import_json(json_str)
    assert restored[0].embedding is not None
    for a, b in zip(emb, restored[0].embedding):
        assert abs(a - b) < 1e-5


def test_export_without_embeddings(serializer):
    """include_embeddings=False should exclude embeddings."""
    emb = _fake_embedding(1.0)
    item = _make_item("No emb export", embedding=emb)
    json_str = serializer.export_json([item], include_embeddings=False)
    data = json.loads(json_str)
    assert "embedding_b64" not in data["items"][0]


def test_import_without_embeddings(serializer):
    """Import items without embedding_b64 should have None embedding."""
    item = _make_item("No embedding")
    json_str = serializer.export_json([item], include_embeddings=False)
    restored = serializer.import_json(json_str)
    assert restored[0].embedding is None


def test_snapshot(serializer):
    """snapshot should create MemorySnapshot with zone distribution."""
    items = [
        _make_item("A", zone=0),
        _make_item("B", zone=0),
        _make_item("C", zone=1),
    ]
    snap = serializer.snapshot(items)
    assert isinstance(snap, MemorySnapshot)
    assert snap.total_memories == 3
    assert snap.zone_distribution[0] == 2
    assert snap.zone_distribution[1] == 1


def test_empty_export_import(serializer):
    """Empty list should export and import cleanly."""
    json_str = serializer.export_json([])
    data = json.loads(json_str)
    assert data["count"] == 0
    restored = serializer.import_json(json_str)
    assert restored == []


def test_stellar_export_import(tmp_path):
    """StellarMemory.export_json/import_json integration."""
    config = StellarConfig(db_path=str(tmp_path / "test.db"))
    mem = StellarMemory(config)
    mem.store("Export test memory A")
    mem.store("Export test memory B")
    json_str = mem.export_json(include_embeddings=False)
    data = json.loads(json_str)
    assert data["count"] == 2

    # Import into fresh instance
    config2 = StellarConfig(db_path=str(tmp_path / "test2.db"))
    mem2 = StellarMemory(config2)
    count = mem2.import_json(json_str)
    assert count == 2
    assert mem2.stats().total_memories == 2


def test_stellar_snapshot(tmp_path):
    """StellarMemory.snapshot() should return valid snapshot."""
    config = StellarConfig(db_path=str(tmp_path / "test.db"))
    mem = StellarMemory(config)
    mem.store("Snapshot item")
    snap = mem.snapshot()
    assert isinstance(snap, MemorySnapshot)
    assert snap.total_memories == 1
    assert snap.version == "0.3.0"
