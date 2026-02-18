"""Tests for P5-F5: Graph Analytics."""

from __future__ import annotations

import pytest

from stellar_memory.graph_analyzer import GraphAnalyzer, GraphStats, CentralityResult
from stellar_memory.memory_graph import MemoryGraph
from stellar_memory.config import GraphAnalyticsConfig, StellarConfig
from stellar_memory.models import MemoryItem
from stellar_memory.stellar import StellarMemory


def _build_graph() -> MemoryGraph:
    """Build a test graph: A-B-C-D, A-C (triangle A-B-C + chain C-D)."""
    g = MemoryGraph(max_edges_per_item=20)
    g.add_edge("A", "B", "related_to")
    g.add_edge("B", "C", "related_to")
    g.add_edge("A", "C", "related_to")
    g.add_edge("C", "D", "related_to")
    return g


class TestGraphStats:
    def test_stats_basic(self):
        g = _build_graph()
        analyzer = GraphAnalyzer(g, GraphAnalyticsConfig())
        stats = analyzer.stats()
        assert stats.total_nodes == 4
        assert stats.total_edges == 4
        assert stats.connected_components == 1
        assert stats.density > 0

    def test_stats_empty_graph(self):
        g = MemoryGraph(max_edges_per_item=20)
        analyzer = GraphAnalyzer(g, GraphAnalyticsConfig())
        stats = analyzer.stats()
        assert stats.total_nodes == 0
        assert stats.total_edges == 0
        assert stats.avg_degree == 0.0

    def test_stats_disconnected(self):
        g = MemoryGraph(max_edges_per_item=20)
        g.add_edge("A", "B", "related_to")
        g.add_edge("C", "D", "related_to")
        analyzer = GraphAnalyzer(g, GraphAnalyticsConfig())
        stats = analyzer.stats()
        assert stats.connected_components == 2


class TestCentrality:
    def test_centrality_order(self):
        g = _build_graph()
        analyzer = GraphAnalyzer(g, GraphAnalyticsConfig())
        results = analyzer.centrality(top_k=4)
        assert len(results) == 4
        # C has highest degree (connected to A, B, D)
        assert results[0].item_id == "C"

    def test_centrality_top_k(self):
        g = _build_graph()
        analyzer = GraphAnalyzer(g, GraphAnalyticsConfig())
        results = analyzer.centrality(top_k=2)
        assert len(results) == 2

    def test_centrality_score_normalized(self):
        g = _build_graph()
        analyzer = GraphAnalyzer(g, GraphAnalyticsConfig())
        results = analyzer.centrality(top_k=4)
        assert results[0].score == 1.0  # Highest node has score 1.0


class TestCommunities:
    def test_single_component(self):
        g = _build_graph()
        config = GraphAnalyticsConfig(community_min_size=2)
        analyzer = GraphAnalyzer(g, config)
        comms = analyzer.communities()
        assert len(comms) == 1
        assert len(comms[0]) == 4

    def test_two_components(self):
        g = MemoryGraph(max_edges_per_item=20)
        g.add_edge("A", "B", "related_to")
        g.add_edge("C", "D", "related_to")
        config = GraphAnalyticsConfig(community_min_size=2)
        analyzer = GraphAnalyzer(g, config)
        comms = analyzer.communities()
        assert len(comms) == 2

    def test_min_size_filter(self):
        g = MemoryGraph(max_edges_per_item=20)
        g.add_edge("A", "B", "related_to")
        g.add_edge("C", "D", "related_to")
        g.add_edge("D", "E", "related_to")
        config = GraphAnalyticsConfig(community_min_size=3)
        analyzer = GraphAnalyzer(g, config)
        comms = analyzer.communities()
        # Only {C, D, E} meets min_size=3
        assert len(comms) == 1
        assert len(comms[0]) == 3

    def test_empty_graph(self):
        g = MemoryGraph(max_edges_per_item=20)
        analyzer = GraphAnalyzer(g, GraphAnalyticsConfig())
        comms = analyzer.communities()
        assert comms == []


class TestPath:
    def test_path_exists(self):
        g = _build_graph()
        analyzer = GraphAnalyzer(g, GraphAnalyticsConfig())
        p = analyzer.path("A", "D")
        assert p is not None
        assert p[0] == "A"
        assert p[-1] == "D"
        assert len(p) <= 4  # At most A → C → D (length 2)

    def test_direct_path(self):
        g = _build_graph()
        analyzer = GraphAnalyzer(g, GraphAnalyticsConfig())
        p = analyzer.path("A", "B")
        assert p == ["A", "B"]

    def test_no_path(self):
        g = MemoryGraph(max_edges_per_item=20)
        g.add_edge("A", "B", "related_to")
        g.add_edge("C", "D", "related_to")
        analyzer = GraphAnalyzer(g, GraphAnalyticsConfig())
        p = analyzer.path("A", "C")
        assert p is None

    def test_path_to_self(self):
        g = _build_graph()
        analyzer = GraphAnalyzer(g, GraphAnalyticsConfig())
        p = analyzer.path("A", "A")
        assert p == ["A"]


class TestExportDot:
    def test_dot_format(self):
        g = _build_graph()
        analyzer = GraphAnalyzer(g, GraphAnalyticsConfig())
        dot = analyzer.export_dot()
        assert "digraph StellarMemory" in dot
        assert "rankdir=LR" in dot
        assert "->" in dot

    def test_dot_with_memory_getter(self):
        g = MemoryGraph(max_edges_per_item=20)
        g.add_edge("id-001", "id-002", "related_to")
        analyzer = GraphAnalyzer(g, GraphAnalyticsConfig())

        def getter(id):
            m = MemoryItem.create("content for " + id[:8])
            m.id = id
            return m

        dot = analyzer.export_dot(memory_getter=getter)
        assert "content for" in dot


class TestExportGraphml:
    def test_graphml_format(self):
        g = _build_graph()
        analyzer = GraphAnalyzer(g, GraphAnalyticsConfig())
        gml = analyzer.export_graphml()
        assert '<?xml version="1.0"' in gml
        assert "<graphml" in gml
        assert "<node" in gml
        assert "<edge" in gml


class TestStellarMemoryGraphAnalytics:
    def _make_memory(self) -> StellarMemory:
        config = StellarConfig(db_path=":memory:")
        config.graph.persistent = False
        config.graph.auto_link = False
        config.embedder.enabled = False
        config.event_logger.enabled = False
        config.graph_analytics.enabled = True
        return StellarMemory(config)

    def test_analyzer_enabled(self):
        mem = self._make_memory()
        assert mem._analyzer is not None

    def test_analyzer_disabled(self):
        config = StellarConfig(db_path=":memory:")
        config.graph.persistent = False
        config.embedder.enabled = False
        config.event_logger.enabled = False
        config.graph_analytics.enabled = False
        mem = StellarMemory(config)
        assert mem._analyzer is None

    def test_graph_stats_method(self):
        mem = self._make_memory()
        stats = mem.graph_stats()
        assert stats.total_nodes == 0

    def test_graph_stats_not_enabled_raises(self):
        config = StellarConfig(db_path=":memory:")
        config.graph.persistent = False
        config.embedder.enabled = False
        config.event_logger.enabled = False
        config.graph_analytics.enabled = False
        mem = StellarMemory(config)
        with pytest.raises(RuntimeError, match="Graph analytics not enabled"):
            mem.graph_stats()
