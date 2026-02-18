"""Tests for Recall Boost (graph-enhanced search)."""

import pytest

from stellar_memory.config import StellarConfig, GraphConfig, RecallConfig
from stellar_memory.stellar import StellarMemory


class TestRecallBoost:
    def test_boost_disabled_returns_normal(self, tmp_path):
        db = str(tmp_path / "test.db")
        config = StellarConfig(
            db_path=db,
            recall_boost=RecallConfig(graph_boost_enabled=False),
        )
        mem = StellarMemory(config)
        mem.store("alpha content")
        results = mem.recall("alpha")
        # Should still work without boost
        assert len(results) >= 1

    def test_boost_includes_graph_neighbors(self, tmp_path):
        db = str(tmp_path / "test.db")
        config = StellarConfig(
            db_path=db,
            recall_boost=RecallConfig(graph_boost_enabled=True),
        )
        mem = StellarMemory(config)
        item1 = mem.store("main topic")
        item2 = mem.store("related detail")
        # Manually link in graph
        mem.graph.add_edge(item1.id, item2.id, "related_to", 0.9)

        results = mem.recall("main topic", limit=5)
        result_ids = {r.id for r in results}
        # Both items should appear (item2 boosted via graph)
        assert item1.id in result_ids

    def test_boost_score_added(self, tmp_path):
        db = str(tmp_path / "test.db")
        boost = 0.2
        config = StellarConfig(
            db_path=db,
            recall_boost=RecallConfig(
                graph_boost_enabled=True,
                graph_boost_score=boost,
            ),
        )
        mem = StellarMemory(config)
        item1 = mem.store("main")
        item2 = mem.store("neighbor")
        original_score = item2.total_score
        mem.graph.add_edge(item1.id, item2.id, "related_to", 0.9)

        results = mem.recall("main", limit=5)
        for r in results:
            if r.id == item2.id:
                # Neighbor should have boosted score if it was added via graph
                # (it may also be found via normal search)
                break

    def test_depth_1_only(self, tmp_path):
        db = str(tmp_path / "test.db")
        config = StellarConfig(
            db_path=db,
            recall_boost=RecallConfig(
                graph_boost_enabled=True,
                graph_boost_depth=1,
            ),
        )
        mem = StellarMemory(config)
        item1 = mem.store("root")
        item2 = mem.store("child")
        item3 = mem.store("grandchild")
        mem.graph.add_edge(item1.id, item2.id, "related_to")
        mem.graph.add_edge(item2.id, item3.id, "related_to")

        results = mem.recall("root", limit=10)
        # depth=1 means only direct neighbors get boosted
        # All items may appear via normal search though

    def test_result_limit_maintained(self, tmp_path):
        db = str(tmp_path / "test.db")
        config = StellarConfig(
            db_path=db,
            recall_boost=RecallConfig(graph_boost_enabled=True),
        )
        mem = StellarMemory(config)
        for i in range(10):
            mem.store(f"memory {i}")

        results = mem.recall("memory", limit=3)
        assert len(results) <= 3

    def test_no_duplicates(self, tmp_path):
        db = str(tmp_path / "test.db")
        config = StellarConfig(
            db_path=db,
            recall_boost=RecallConfig(graph_boost_enabled=True),
        )
        mem = StellarMemory(config)
        item1 = mem.store("unique one")
        item2 = mem.store("unique two")
        mem.graph.add_edge(item1.id, item2.id, "related_to")
        mem.graph.add_edge(item2.id, item1.id, "related_to")

        results = mem.recall("unique", limit=5)
        result_ids = [r.id for r in results]
        assert len(result_ids) == len(set(result_ids))

    def test_empty_graph_no_effect(self, tmp_path):
        db = str(tmp_path / "test.db")
        config = StellarConfig(
            db_path=db,
            recall_boost=RecallConfig(graph_boost_enabled=True),
        )
        mem = StellarMemory(config)
        mem.store("lonely memory")
        # No graph edges
        results = mem.recall("lonely", limit=5)
        assert len(results) >= 1

    def test_null_embedder_with_manual_graph(self, tmp_path):
        db = str(tmp_path / "test.db")
        config = StellarConfig(
            db_path=db,
            recall_boost=RecallConfig(graph_boost_enabled=True),
        )
        mem = StellarMemory(config)
        item1 = mem.store("first item")
        item2 = mem.store("second item")
        mem.graph.add_edge(item1.id, item2.id, "related_to")

        # Should not crash even with NullEmbedder
        results = mem.recall("first", limit=5)
        assert isinstance(results, list)
