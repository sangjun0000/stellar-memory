"""Tests for MCP server tools (unit tests without actual MCP transport)."""

import json
import pytest

from stellar_memory.config import StellarConfig
from stellar_memory.stellar import StellarMemory


class TestMCPServerLogic:
    """Test MCP tool logic directly via StellarMemory (no mcp dependency needed)."""

    def setup_method(self):
        self.config = StellarConfig(db_path=":memory:")
        self.memory = StellarMemory(self.config)

    def test_memory_store(self):
        item = self.memory.store("test content", importance=0.7)
        assert item.id is not None
        assert item.content == "test content"

    def test_memory_recall(self):
        self.memory.store("the quick brown fox")
        results = self.memory.recall("fox", limit=5)
        assert len(results) >= 1
        assert any("fox" in r.content for r in results)

    def test_memory_get(self):
        item = self.memory.store("get me")
        found = self.memory.get(item.id)
        assert found is not None
        assert found.content == "get me"

    def test_memory_get_not_found(self):
        found = self.memory.get("nonexistent-id")
        assert found is None

    def test_memory_forget(self):
        item = self.memory.store("to delete")
        assert self.memory.forget(item.id) is True
        assert self.memory.get(item.id) is None

    def test_memory_stats(self):
        self.memory.store("stat item")
        stats = self.memory.stats()
        assert stats.total_memories >= 1

    def test_session_start_and_end(self):
        session = self.memory.start_session()
        assert session.session_id != ""
        ended = self.memory.end_session()
        assert ended is not None
        assert ended.session_id == session.session_id

    def test_memory_export(self):
        self.memory.store("export me")
        data = self.memory.export_json(include_embeddings=False)
        parsed = json.loads(data)
        assert len(parsed["items"]) >= 1

    def test_memory_import(self):
        self.memory.store("original")
        exported = self.memory.export_json(include_embeddings=False)
        # Create fresh instance and import
        config2 = StellarConfig(db_path=":memory:")
        mem2 = StellarMemory(config2)
        count = mem2.import_json(exported)
        assert count >= 1

    def test_stats_zone_info(self):
        self.memory.store("zone info test", importance=0.9)
        stats = self.memory.stats()
        assert isinstance(stats.zone_counts, dict)
        assert isinstance(stats.zone_capacities, dict)
        assert len(stats.zone_counts) > 0
