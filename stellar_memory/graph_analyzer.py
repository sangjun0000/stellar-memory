"""Graph analytics for memory relationship analysis."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field

from stellar_memory.config import GraphAnalyticsConfig
from stellar_memory.models import MemoryEdge

logger = logging.getLogger(__name__)


@dataclass
class GraphStats:
    total_nodes: int = 0
    total_edges: int = 0
    avg_degree: float = 0.0
    density: float = 0.0
    connected_components: int = 0


@dataclass
class CentralityResult:
    item_id: str = ""
    degree: int = 0
    score: float = 0.0


class GraphAnalyzer:
    """Analyzes memory graph structure and patterns."""

    def __init__(self, graph, config: GraphAnalyticsConfig):
        self._graph = graph
        self._config = config

    def stats(self) -> GraphStats:
        """Compute graph-level statistics."""
        all_edges = self._get_all_edges()
        nodes: set[str] = set()
        for edge in all_edges:
            nodes.add(edge.source_id)
            nodes.add(edge.target_id)
        n = len(nodes)
        e = len(all_edges)
        avg_deg = (2 * e / n) if n > 0 else 0.0
        density = (2 * e / (n * (n - 1))) if n > 1 else 0.0
        components = self._count_components(nodes, all_edges)
        return GraphStats(
            total_nodes=n, total_edges=e,
            avg_degree=avg_deg, density=density,
            connected_components=components,
        )

    def centrality(self, top_k: int = 10) -> list[CentralityResult]:
        """Degree centrality for all nodes. Returns top-k sorted descending."""
        all_edges = self._get_all_edges()
        degree_map: dict[str, int] = defaultdict(int)
        for edge in all_edges:
            degree_map[edge.source_id] += 1
            degree_map[edge.target_id] += 1
        max_degree = max(degree_map.values()) if degree_map else 1
        results = [
            CentralityResult(
                item_id=item_id,
                degree=deg,
                score=deg / max_degree,
            )
            for item_id, deg in degree_map.items()
        ]
        results.sort(key=lambda x: x.degree, reverse=True)
        return results[:top_k]

    def communities(self) -> list[list[str]]:
        """Detect communities using connected components."""
        all_edges = self._get_all_edges()
        nodes: set[str] = set()
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in all_edges:
            nodes.add(edge.source_id)
            nodes.add(edge.target_id)
            adjacency[edge.source_id].add(edge.target_id)
            adjacency[edge.target_id].add(edge.source_id)

        visited: set[str] = set()
        communities: list[list[str]] = []
        for node in nodes:
            if node in visited:
                continue
            component = self._bfs_component(node, adjacency, visited)
            if len(component) >= self._config.community_min_size:
                communities.append(sorted(component))

        communities.sort(key=len, reverse=True)
        return communities

    def path(self, source_id: str, target_id: str,
             max_depth: int = 10) -> list[str] | None:
        """Find shortest path between two memories using BFS."""
        all_edges = self._get_all_edges()
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in all_edges:
            adjacency[edge.source_id].add(edge.target_id)
            adjacency[edge.target_id].add(edge.source_id)

        visited = {source_id}
        parent: dict[str, str | None] = {source_id: None}
        queue = [(source_id, 0)]
        while queue:
            current, depth = queue.pop(0)
            if current == target_id:
                result = []
                node: str | None = target_id
                while node is not None:
                    result.append(node)
                    node = parent[node]
                return list(reversed(result))
            if depth >= max_depth:
                continue
            for neighbor in adjacency.get(current, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append((neighbor, depth + 1))
        return None

    def export_dot(self, memory_getter=None) -> str:
        """Export graph in DOT format for Graphviz."""
        all_edges = self._get_all_edges()
        lines = ["digraph StellarMemory {"]
        lines.append("  rankdir=LR;")
        nodes: set[str] = set()
        for edge in all_edges:
            nodes.add(edge.source_id)
            nodes.add(edge.target_id)
        for node_id in sorted(nodes):
            label = node_id[:8]
            if memory_getter:
                item = memory_getter(node_id)
                if item:
                    label = item.content[:30].replace('"', '\\"')
            lines.append(f'  "{node_id[:8]}" [label="{label}"];')
        for edge in all_edges:
            lines.append(
                f'  "{edge.source_id[:8]}" -> "{edge.target_id[:8]}" '
                f'[label="{edge.edge_type}"];'
            )
        lines.append("}")
        return "\n".join(lines)

    def export_graphml(self) -> str:
        """Export graph in GraphML format."""
        all_edges = self._get_all_edges()
        nodes: set[str] = set()
        for edge in all_edges:
            nodes.add(edge.source_id)
            nodes.add(edge.target_id)
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append('<graphml xmlns="http://graphml.graphstruct.org/graphml">')
        lines.append('  <graph id="stellar-memory" edgedefault="directed">')
        for node_id in sorted(nodes):
            lines.append(f'    <node id="{node_id}"/>')
        for i, edge in enumerate(all_edges):
            lines.append(
                f'    <edge id="e{i}" source="{edge.source_id}" '
                f'target="{edge.target_id}"/>'
            )
        lines.append("  </graph>")
        lines.append("</graphml>")
        return "\n".join(lines)

    # --- Internal helpers ---

    def _get_all_edges(self) -> list[MemoryEdge]:
        """Get all edges from graph (works with both graph types)."""
        if hasattr(self._graph, "_edges"):
            # In-memory MemoryGraph
            edges = []
            for edge_list in self._graph._edges.values():
                edges.extend(edge_list)
            return edges
        elif hasattr(self._graph, "_get_conn"):
            # PersistentMemoryGraph
            conn = self._graph._get_conn()
            cur = conn.execute(
                "SELECT source_id, target_id, edge_type, weight, created_at "
                "FROM edges"
            )
            return [
                MemoryEdge(
                    source_id=r[0], target_id=r[1], edge_type=r[2],
                    weight=r[3], created_at=r[4],
                )
                for r in cur.fetchall()
            ]
        return []

    def _count_components(self, nodes, edges) -> int:
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in edges:
            adjacency[edge.source_id].add(edge.target_id)
            adjacency[edge.target_id].add(edge.source_id)
        visited: set[str] = set()
        count = 0
        for node in nodes:
            if node not in visited:
                self._bfs_component(node, adjacency, visited)
                count += 1
        return count

    def _bfs_component(self, start: str, adjacency: dict[str, set[str]],
                       visited: set[str]) -> list[str]:
        component = []
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            component.append(node)
            for neighbor in adjacency.get(node, set()):
                if neighbor not in visited:
                    queue.append(neighbor)
        return component
