"""Vector index for scalable similarity search."""

from __future__ import annotations

import logging
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from stellar_memory.utils import cosine_similarity

logger = logging.getLogger(__name__)


class VectorIndex(ABC):
    """Abstract base for vector search indices."""

    @abstractmethod
    def add(self, item_id: str, vector: list[float]) -> None: ...

    @abstractmethod
    def remove(self, item_id: str) -> None: ...

    @abstractmethod
    def search(self, query_vector: list[float], top_k: int = 10) -> list[tuple[str, float]]:
        """Returns list of (item_id, similarity_score) sorted descending."""
        ...

    @abstractmethod
    def size(self) -> int: ...

    def rebuild(self, items: dict[str, list[float]]) -> None:
        """Rebuild index from scratch."""
        for item_id, vector in items.items():
            self.add(item_id, vector)


class BruteForceIndex(VectorIndex):
    """O(n) brute force search - wraps cosine_similarity."""

    def __init__(self):
        self._vectors: dict[str, list[float]] = {}

    def add(self, item_id: str, vector: list[float]) -> None:
        self._vectors[item_id] = vector

    def remove(self, item_id: str) -> None:
        self._vectors.pop(item_id, None)

    def search(self, query_vector: list[float], top_k: int = 10) -> list[tuple[str, float]]:
        scores = []
        for item_id, vec in self._vectors.items():
            sim = cosine_similarity(query_vector, vec)
            scores.append((item_id, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def size(self) -> int:
        return len(self._vectors)

    def rebuild(self, items: dict[str, list[float]]) -> None:
        self._vectors = dict(items)


# --- Ball Tree Implementation ---

@dataclass
class _BallTreeNode:
    centroid: list[float]
    radius: float
    item_ids: list[str] | None = None
    vectors: list[list[float]] | None = None
    left: _BallTreeNode | None = None
    right: _BallTreeNode | None = None


def _euclidean_dist(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _centroid(vectors: list[list[float]]) -> list[float]:
    n = len(vectors)
    dim = len(vectors[0])
    c = [0.0] * dim
    for v in vectors:
        for i in range(dim):
            c[i] += v[i]
    return [x / n for x in c]


class BallTreeIndex(VectorIndex):
    """Ball-Tree based approximate nearest neighbor search.
    Pure Python. O(log n) average case."""

    def __init__(self, leaf_size: int = 40):
        self._leaf_size = leaf_size
        self._vectors: dict[str, list[float]] = {}
        self._tree: _BallTreeNode | None = None
        self._dirty = True

    def add(self, item_id: str, vector: list[float]) -> None:
        self._vectors[item_id] = vector
        self._dirty = True

    def remove(self, item_id: str) -> None:
        self._vectors.pop(item_id, None)
        self._dirty = True

    def search(self, query_vector: list[float], top_k: int = 10) -> list[tuple[str, float]]:
        if not self._vectors:
            return []
        if self._dirty or self._tree is None:
            self._build_tree()
        # Collect candidates, then compute cosine similarity
        candidates = self._tree_search(query_vector, top_k)
        return candidates

    def size(self) -> int:
        return len(self._vectors)

    def rebuild(self, items: dict[str, list[float]]) -> None:
        self._vectors = dict(items)
        self._dirty = True

    def _build_tree(self) -> None:
        if not self._vectors:
            self._tree = None
            self._dirty = False
            return
        ids = list(self._vectors.keys())
        vecs = [self._vectors[i] for i in ids]
        self._tree = self._build_node(ids, vecs)
        self._dirty = False

    def _build_node(self, ids: list[str], vecs: list[list[float]]) -> _BallTreeNode:
        c = _centroid(vecs)
        radius = max(_euclidean_dist(c, v) for v in vecs) if vecs else 0.0

        if len(ids) <= self._leaf_size:
            return _BallTreeNode(centroid=c, radius=radius,
                                 item_ids=ids, vectors=vecs)

        # Split by dimension with largest spread
        dim = len(vecs[0])
        best_dim = 0
        best_spread = 0.0
        for d in range(dim):
            vals = [v[d] for v in vecs]
            spread = max(vals) - min(vals)
            if spread > best_spread:
                best_spread = spread
                best_dim = d

        paired = list(zip(ids, vecs))
        paired.sort(key=lambda x: x[1][best_dim])
        mid = len(paired) // 2

        left_ids = [p[0] for p in paired[:mid]]
        left_vecs = [p[1] for p in paired[:mid]]
        right_ids = [p[0] for p in paired[mid:]]
        right_vecs = [p[1] for p in paired[mid:]]

        node = _BallTreeNode(centroid=c, radius=radius)
        node.left = self._build_node(left_ids, left_vecs)
        node.right = self._build_node(right_ids, right_vecs)
        return node

    def _tree_search(self, query: list[float], top_k: int) -> list[tuple[str, float]]:
        """Search tree using branch-and-bound."""
        results: list[tuple[str, float]] = []
        worst_score = -1.0

        def _search_node(node: _BallTreeNode | None) -> None:
            nonlocal worst_score
            if node is None:
                return

            # Prune: if centroid distance - radius can't beat worst
            dist_to_centroid = _euclidean_dist(query, node.centroid)
            if len(results) >= top_k:
                # Heuristic prune using distance
                if dist_to_centroid - node.radius > 2.0:  # rough threshold
                    return

            if node.item_ids is not None:
                # Leaf node
                for item_id, vec in zip(node.item_ids, node.vectors):
                    sim = cosine_similarity(query, vec)
                    if len(results) < top_k:
                        results.append((item_id, sim))
                        results.sort(key=lambda x: x[1], reverse=True)
                        if len(results) >= top_k:
                            worst_score = results[-1][1]
                    elif sim > worst_score:
                        results[-1] = (item_id, sim)
                        results.sort(key=lambda x: x[1], reverse=True)
                        worst_score = results[-1][1]
                return

            # Visit closer child first
            left_dist = _euclidean_dist(query, node.left.centroid) if node.left else float('inf')
            right_dist = _euclidean_dist(query, node.right.centroid) if node.right else float('inf')

            if left_dist <= right_dist:
                _search_node(node.left)
                _search_node(node.right)
            else:
                _search_node(node.right)
                _search_node(node.left)

        _search_node(self._tree)
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


def create_vector_index(config, dimension: int = 384) -> VectorIndex:
    """Factory: create the appropriate vector index."""
    from stellar_memory.config import VectorIndexConfig
    if not isinstance(config, VectorIndexConfig):
        return BruteForceIndex()
    if not config.enabled:
        return BruteForceIndex()
    if config.backend == "ball_tree":
        return BallTreeIndex(leaf_size=config.ball_tree_leaf_size)
    elif config.backend == "faiss":
        try:
            from stellar_memory.faiss_index import FaissIndex
            return FaissIndex(dimension=dimension)
        except ImportError:
            logger.warning("faiss not installed, falling back to BallTreeIndex")
            return BallTreeIndex(leaf_size=config.ball_tree_leaf_size)
    else:
        return BruteForceIndex()
