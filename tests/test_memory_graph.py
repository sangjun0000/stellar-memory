"""Tests for MemoryGraph and StellarMemory graph integration."""

import pytest

from stellar_memory.memory_graph import MemoryGraph
from stellar_memory.models import MemoryEdge
from stellar_memory.config import StellarConfig, GraphConfig
from stellar_memory.stellar import StellarMemory


class TestMemoryGraph:
    def test_add_edge(self):
        g = MemoryGraph()
        edge = g.add_edge("a", "b", "related_to", 0.9)
        assert edge.source_id == "a"
        assert edge.target_id == "b"
        assert edge.weight == 0.9

    def test_get_edges(self):
        g = MemoryGraph()
        g.add_edge("a", "b")
        g.add_edge("a", "c")
        edges = g.get_edges("a")
        assert len(edges) == 2
        targets = {e.target_id for e in edges}
        assert targets == {"b", "c"}

    def test_get_related_ids_depth_1(self):
        g = MemoryGraph()
        g.add_edge("a", "b")
        g.add_edge("a", "c")
        g.add_edge("b", "d")  # depth 2 from a
        related = g.get_related_ids("a", depth=1)
        assert related == {"b", "c"}

    def test_get_related_ids_depth_2(self):
        g = MemoryGraph()
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        g.add_edge("c", "d")  # depth 3 from a
        related = g.get_related_ids("a", depth=2)
        assert related == {"b", "c"}

    def test_max_edges_per_item(self):
        g = MemoryGraph(max_edges_per_item=3)
        g.add_edge("a", "b", weight=0.5)
        g.add_edge("a", "c", weight=0.8)
        g.add_edge("a", "d", weight=0.9)
        # This should evict lowest weight (0.5 -> "b")
        g.add_edge("a", "e", weight=0.7)
        edges = g.get_edges("a")
        assert len(edges) == 3
        targets = {e.target_id for e in edges}
        assert "b" not in targets
        assert targets == {"c", "d", "e"}

    def test_remove_item(self):
        g = MemoryGraph()
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        g.add_edge("c", "a")
        g.remove_item("a")
        assert g.get_edges("a") == []
        # "c" -> "a" edge should also be removed
        c_edges = g.get_edges("c")
        assert all(e.target_id != "a" for e in c_edges)

    def test_count_edges(self):
        g = MemoryGraph()
        g.add_edge("a", "b")
        g.add_edge("a", "c")
        g.add_edge("b", "c")
        assert g.count_edges() == 3

    def test_stellar_recall_graph(self):
        config = StellarConfig(db_path=":memory:")
        mem = StellarMemory(config)
        item1 = mem.store("memory one")
        item2 = mem.store("memory two")
        # Manually add graph edge
        mem.graph.add_edge(item1.id, item2.id, "related_to", 0.9)
        related = mem.recall_graph(item1.id, depth=1)
        assert len(related) == 1
        assert related[0].id == item2.id

    def test_auto_link_skips_without_embedding(self):
        # With NullEmbedder (no embedding), auto_link should silently skip
        config = StellarConfig(db_path=":memory:")
        mem = StellarMemory(config)
        mem.store("content a")
        mem.store("content b")
        # NullEmbedder produces None embeddings, so no edges created
        assert mem.graph.count_edges() == 0

    def test_forget_cleans_graph(self):
        config = StellarConfig(db_path=":memory:")
        mem = StellarMemory(config)
        item1 = mem.store("first")
        item2 = mem.store("second")
        mem.graph.add_edge(item1.id, item2.id, "related_to")
        mem.forget(item1.id)
        assert mem.graph.get_edges(item1.id) == []
