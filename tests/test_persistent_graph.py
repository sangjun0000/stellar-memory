"""Tests for PersistentMemoryGraph and StellarMemory graph persistence."""

import os
import tempfile

import pytest

from stellar_memory.persistent_graph import PersistentMemoryGraph
from stellar_memory.memory_graph import MemoryGraph
from stellar_memory.config import StellarConfig, GraphConfig
from stellar_memory.stellar import StellarMemory


class TestPersistentMemoryGraph:
    def test_add_edge(self, tmp_path):
        db = str(tmp_path / "test.db")
        g = PersistentMemoryGraph(db)
        edge = g.add_edge("a", "b", "related_to", 0.9)
        assert edge.source_id == "a"
        assert edge.target_id == "b"
        assert edge.weight == 0.9

    def test_get_edges(self, tmp_path):
        db = str(tmp_path / "test.db")
        g = PersistentMemoryGraph(db)
        g.add_edge("a", "b")
        g.add_edge("a", "c")
        edges = g.get_edges("a")
        assert len(edges) == 2
        targets = {e.target_id for e in edges}
        assert targets == {"b", "c"}

    def test_get_related_ids_depth_1(self, tmp_path):
        db = str(tmp_path / "test.db")
        g = PersistentMemoryGraph(db)
        g.add_edge("a", "b")
        g.add_edge("a", "c")
        g.add_edge("b", "d")  # depth 2 from a
        related = g.get_related_ids("a", depth=1)
        assert related == {"b", "c"}

    def test_get_related_ids_depth_2(self, tmp_path):
        db = str(tmp_path / "test.db")
        g = PersistentMemoryGraph(db)
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        g.add_edge("c", "d")  # depth 3 from a
        related = g.get_related_ids("a", depth=2)
        assert related == {"b", "c"}

    def test_max_edges_eviction(self, tmp_path):
        db = str(tmp_path / "test.db")
        g = PersistentMemoryGraph(db, max_edges_per_item=3)
        g.add_edge("a", "b", weight=0.5)
        g.add_edge("a", "c", weight=0.8)
        g.add_edge("a", "d", weight=0.9)
        # Should evict lowest weight (0.5 -> "b")
        g.add_edge("a", "e", weight=0.7)
        edges = g.get_edges("a")
        assert len(edges) == 3
        targets = {e.target_id for e in edges}
        assert "b" not in targets

    def test_remove_item(self, tmp_path):
        db = str(tmp_path / "test.db")
        g = PersistentMemoryGraph(db)
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        g.add_edge("c", "a")
        g.remove_item("a")
        assert g.get_edges("a") == []
        # "c" -> "a" edge should also be removed
        c_edges = g.get_edges("c")
        assert all(e.target_id != "a" for e in c_edges)

    def test_count_edges(self, tmp_path):
        db = str(tmp_path / "test.db")
        g = PersistentMemoryGraph(db)
        g.add_edge("a", "b")
        g.add_edge("a", "c")
        g.add_edge("b", "c")
        assert g.count_edges() == 3

    def test_persistence_after_restart(self, tmp_path):
        db = str(tmp_path / "test.db")
        # Create graph and add edges
        g1 = PersistentMemoryGraph(db)
        g1.add_edge("x", "y", "related_to", 0.85)
        g1.add_edge("x", "z", "derived_from", 0.6)
        assert g1.count_edges() == 2

        # Create new instance (simulate restart)
        g2 = PersistentMemoryGraph(db)
        assert g2.count_edges() == 2
        edges = g2.get_edges("x")
        assert len(edges) == 2
        targets = {e.target_id for e in edges}
        assert targets == {"y", "z"}

    def test_stellar_uses_persistent_graph(self, tmp_path):
        db = str(tmp_path / "test.db")
        config = StellarConfig(
            db_path=db,
            graph=GraphConfig(persistent=True),
        )
        mem = StellarMemory(config)
        assert isinstance(mem._graph, PersistentMemoryGraph)

    def test_memory_db_uses_in_memory_graph(self):
        config = StellarConfig(
            db_path=":memory:",
            graph=GraphConfig(persistent=True),
        )
        mem = StellarMemory(config)
        assert isinstance(mem._graph, MemoryGraph)
