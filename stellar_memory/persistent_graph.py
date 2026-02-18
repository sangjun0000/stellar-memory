"""Persistent memory graph using SQLite."""

from __future__ import annotations

import sqlite3
import threading
import time

from stellar_memory.models import MemoryEdge


class PersistentMemoryGraph:
    """SQLite-backed memory graph that survives restarts."""

    def __init__(self, db_path: str, max_edges_per_item: int = 20):
        self._db_path = db_path
        self._max_edges = max_edges_per_item
        self._local = threading.local()
        self._init_table()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path)
            self._local.conn.execute("PRAGMA journal_mode=WAL")
        return self._local.conn

    def _init_table(self) -> None:
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                edge_type TEXT NOT NULL DEFAULT 'related_to',
                weight REAL NOT NULL DEFAULT 1.0,
                created_at REAL NOT NULL,
                PRIMARY KEY (source_id, target_id, edge_type)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)"
        )
        conn.commit()

    def add_edge(self, source_id: str, target_id: str,
                 edge_type: str = "related_to", weight: float = 1.0) -> MemoryEdge:
        """Add a relationship between two memories."""
        conn = self._get_conn()
        now = time.time()

        cur = conn.execute(
            "SELECT COUNT(*) FROM edges WHERE source_id = ?", (source_id,)
        )
        count = cur.fetchone()[0]
        if count >= self._max_edges:
            conn.execute("""
                DELETE FROM edges WHERE rowid IN (
                    SELECT rowid FROM edges WHERE source_id = ?
                    ORDER BY weight ASC LIMIT 1
                )
            """, (source_id,))

        conn.execute(
            "INSERT OR REPLACE INTO edges "
            "(source_id, target_id, edge_type, weight, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (source_id, target_id, edge_type, weight, now),
        )
        conn.commit()
        return MemoryEdge(
            source_id=source_id, target_id=target_id,
            edge_type=edge_type, weight=weight, created_at=now,
        )

    def get_edges(self, item_id: str) -> list[MemoryEdge]:
        """Get all edges from a memory item."""
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT source_id, target_id, edge_type, weight, created_at "
            "FROM edges WHERE source_id = ?", (item_id,)
        )
        return [
            MemoryEdge(
                source_id=row[0], target_id=row[1], edge_type=row[2],
                weight=row[3], created_at=row[4],
            )
            for row in cur.fetchall()
        ]

    def get_related_ids(self, item_id: str, depth: int = 1) -> set[str]:
        """Get IDs of related memories up to a certain depth (BFS)."""
        visited: set[str] = set()
        queue = [(item_id, 0)]
        while queue:
            current_id, current_depth = queue.pop(0)
            if current_id in visited or current_depth > depth:
                continue
            visited.add(current_id)
            if current_depth < depth:
                for edge in self.get_edges(current_id):
                    queue.append((edge.target_id, current_depth + 1))
        visited.discard(item_id)
        return visited

    def remove_item(self, item_id: str) -> None:
        """Remove all edges involving an item."""
        conn = self._get_conn()
        conn.execute("DELETE FROM edges WHERE source_id = ?", (item_id,))
        conn.execute("DELETE FROM edges WHERE target_id = ?", (item_id,))
        conn.commit()

    def count_edges(self) -> int:
        """Total number of edges in the graph."""
        conn = self._get_conn()
        cur = conn.execute("SELECT COUNT(*) FROM edges")
        return cur.fetchone()[0]
