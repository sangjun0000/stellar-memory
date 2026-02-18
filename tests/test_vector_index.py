"""Tests for P5-F2: Vector Index / Scalable Search."""

from __future__ import annotations

import math
import pytest

from stellar_memory.vector_index import (
    BruteForceIndex, BallTreeIndex, create_vector_index,
    _euclidean_dist, _centroid,
)
from stellar_memory.config import VectorIndexConfig


def _make_vector(val: float, dim: int = 8) -> list[float]:
    """Create a simple test vector."""
    return [val] * dim


def _normalize(v: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in v))
    return [x / norm for x in v] if norm > 0 else v


class TestBruteForceIndex:
    def test_add_and_size(self):
        idx = BruteForceIndex()
        assert idx.size() == 0
        idx.add("a", [1.0, 0.0])
        assert idx.size() == 1
        idx.add("b", [0.0, 1.0])
        assert idx.size() == 2

    def test_remove(self):
        idx = BruteForceIndex()
        idx.add("a", [1.0, 0.0])
        idx.add("b", [0.0, 1.0])
        idx.remove("a")
        assert idx.size() == 1
        # Removing non-existent is no-op
        idx.remove("nonexistent")
        assert idx.size() == 1

    def test_search_basic(self):
        idx = BruteForceIndex()
        idx.add("a", [1.0, 0.0])
        idx.add("b", [0.0, 1.0])
        idx.add("c", [0.7, 0.7])
        results = idx.search([1.0, 0.0], top_k=2)
        assert len(results) == 2
        assert results[0][0] == "a"  # Most similar to [1,0]

    def test_search_empty(self):
        idx = BruteForceIndex()
        results = idx.search([1.0, 0.0], top_k=5)
        assert results == []

    def test_rebuild(self):
        idx = BruteForceIndex()
        idx.add("old", [1.0, 0.0])
        idx.rebuild({"new1": [0.5, 0.5], "new2": [0.3, 0.7]})
        assert idx.size() == 2
        results = idx.search([0.5, 0.5], top_k=1)
        assert results[0][0] == "new1"


class TestBallTreeIndex:
    def test_add_and_size(self):
        idx = BallTreeIndex(leaf_size=2)
        assert idx.size() == 0
        for i in range(5):
            idx.add(f"item_{i}", _normalize([float(i), 1.0 - float(i) * 0.1]))
        assert idx.size() == 5

    def test_remove(self):
        idx = BallTreeIndex(leaf_size=2)
        idx.add("a", [1.0, 0.0, 0.0])
        idx.add("b", [0.0, 1.0, 0.0])
        idx.remove("a")
        assert idx.size() == 1

    def test_search_finds_nearest(self):
        idx = BallTreeIndex(leaf_size=2)
        vectors = {
            "a": _normalize([1.0, 0.0, 0.0]),
            "b": _normalize([0.0, 1.0, 0.0]),
            "c": _normalize([0.0, 0.0, 1.0]),
            "d": _normalize([0.9, 0.1, 0.0]),
        }
        for k, v in vectors.items():
            idx.add(k, v)

        results = idx.search(_normalize([1.0, 0.0, 0.0]), top_k=2)
        assert len(results) == 2
        top_ids = [r[0] for r in results]
        assert "a" in top_ids  # Exact match should be found

    def test_search_empty(self):
        idx = BallTreeIndex(leaf_size=2)
        results = idx.search([1.0, 0.0], top_k=5)
        assert results == []

    def test_search_with_many_items(self):
        """Test with enough items to force tree splitting."""
        idx = BallTreeIndex(leaf_size=3)
        for i in range(20):
            angle = 2 * math.pi * i / 20
            vec = _normalize([math.cos(angle), math.sin(angle), 0.1])
            idx.add(f"item_{i}", vec)

        assert idx.size() == 20
        query = _normalize([1.0, 0.0, 0.1])
        results = idx.search(query, top_k=3)
        assert len(results) == 3
        # First result should be item_0 (closest to [1, 0, 0.1])
        assert results[0][0] == "item_0"

    def test_rebuild_clears_tree(self):
        idx = BallTreeIndex(leaf_size=2)
        idx.add("old", [1.0, 0.0])
        idx.rebuild({"new1": [0.5, 0.5], "new2": [0.3, 0.7]})
        assert idx.size() == 2


class TestHelperFunctions:
    def test_euclidean_dist(self):
        assert _euclidean_dist([0, 0], [3, 4]) == 5.0
        assert _euclidean_dist([1, 1], [1, 1]) == 0.0

    def test_centroid(self):
        c = _centroid([[1.0, 2.0], [3.0, 4.0]])
        assert c == [2.0, 3.0]

    def test_centroid_single(self):
        c = _centroid([[5.0, 10.0]])
        assert c == [5.0, 10.0]


class TestCreateVectorIndex:
    def test_brute_force_default(self):
        config = VectorIndexConfig(backend="brute_force")
        idx = create_vector_index(config, dimension=8)
        assert isinstance(idx, BruteForceIndex)

    def test_ball_tree(self):
        config = VectorIndexConfig(backend="ball_tree", ball_tree_leaf_size=10)
        idx = create_vector_index(config, dimension=8)
        assert isinstance(idx, BallTreeIndex)

    def test_disabled_returns_brute_force(self):
        config = VectorIndexConfig(enabled=False)
        idx = create_vector_index(config, dimension=8)
        assert isinstance(idx, BruteForceIndex)

    def test_faiss_fallback(self):
        config = VectorIndexConfig(backend="faiss")
        idx = create_vector_index(config, dimension=8)
        # faiss not installed → falls back to BallTreeIndex
        assert isinstance(idx, BallTreeIndex)

    def test_non_config_returns_brute_force(self):
        idx = create_vector_index("not_a_config", dimension=8)
        assert isinstance(idx, BruteForceIndex)
