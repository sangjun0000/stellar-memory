"""Memory graph for associative recall."""

from __future__ import annotations

import time
from collections import defaultdict

from stellar_memory.models import MemoryEdge


class MemoryGraph:
    """Manages relationships between memories."""

    def __init__(self, max_edges_per_item: int = 20):
        self._max_edges = max_edges_per_item
        self._edges: dict[str, list[MemoryEdge]] = defaultdict(list)

    def add_edge(self, source_id: str, target_id: str,
                 edge_type: str = "related_to", weight: float = 1.0) -> MemoryEdge:
        """Add a relationship between two memories."""
        edge = MemoryEdge(
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            weight=weight,
            created_at=time.time(),
        )
        edges = self._edges[source_id]
        if len(edges) >= self._max_edges:
            edges.sort(key=lambda e: e.weight)
            edges.pop(0)
        edges.append(edge)
        return edge

    def get_edges(self, item_id: str) -> list[MemoryEdge]:
        """Get all edges from a memory item."""
        return list(self._edges.get(item_id, []))

    def get_related_ids(self, item_id: str, depth: int = 1) -> set[str]:
        """Get IDs of related memories up to a certain depth."""
        visited: set[str] = set()
        queue = [(item_id, 0)]
        while queue:
            current_id, current_depth = queue.pop(0)
            if current_id in visited or current_depth > depth:
                continue
            visited.add(current_id)
            if current_depth < depth:
                for edge in self._edges.get(current_id, []):
                    queue.append((edge.target_id, current_depth + 1))
        visited.discard(item_id)
        return visited

    def remove_item(self, item_id: str) -> None:
        """Remove all edges involving an item."""
        self._edges.pop(item_id, None)
        for edges in self._edges.values():
            edges[:] = [e for e in edges if e.target_id != item_id]

    def count_edges(self) -> int:
        """Total number of edges in the graph."""
        return sum(len(edges) for edges in self._edges.values())
