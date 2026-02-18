"""SQLite-based storage for Zone 2+ (Outer, Belt, Cloud)."""

from __future__ import annotations

import json
import sqlite3
import threading

from stellar_memory.storage import ZoneStorage
from stellar_memory.models import MemoryItem


class SqliteStorage(ZoneStorage):
    def __init__(self, db_path: str, zone_id: int):
        self._db_path = db_path
        self._zone_id = zone_id
        self._table = f"memories_zone_{zone_id}"
        self._local = threading.local()
        self._init_table()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path)
            self._local.conn.execute("PRAGMA journal_mode=WAL")
        return self._local.conn

    def _init_table(self) -> None:
        conn = self._get_conn()
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._table} (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                created_at REAL NOT NULL,
                last_recalled_at REAL NOT NULL,
                recall_count INTEGER DEFAULT 0,
                arbitrary_importance REAL DEFAULT 0.5,
                zone INTEGER NOT NULL,
                metadata TEXT,
                embedding BLOB,
                total_score REAL DEFAULT 0.0,
                updated_at REAL NOT NULL DEFAULT 0.0
            )
        """)
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{self._table}_score
            ON {self._table}(zone, total_score)
        """)
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{self._table}_zone
            ON {self._table}(zone)
        """)
        conn.commit()

    def _row_to_item(self, row: tuple) -> MemoryItem:
        # Columns: id, content, created_at, last_recalled_at, recall_count,
        #          arbitrary_importance, zone, metadata, embedding, total_score, updated_at
        embedding = None
        if len(row) > 8 and row[8] is not None:
            from stellar_memory.utils import deserialize_embedding
            embedding = deserialize_embedding(row[8])
        return MemoryItem(
            id=row[0],
            content=row[1],
            created_at=row[2],
            last_recalled_at=row[3],
            recall_count=row[4],
            arbitrary_importance=row[5],
            zone=row[6],
            metadata=json.loads(row[7]) if row[7] else {},
            embedding=embedding,
            total_score=row[9] if len(row) > 9 else 0.0,
        )

    def store(self, item: MemoryItem) -> None:
        import time as _time
        embedding_blob = None
        if item.embedding is not None:
            from stellar_memory.utils import serialize_embedding
            embedding_blob = serialize_embedding(item.embedding)
        conn = self._get_conn()
        conn.execute(
            f"INSERT OR REPLACE INTO {self._table} "
            "(id, content, created_at, last_recalled_at, recall_count, "
            "arbitrary_importance, zone, metadata, embedding, total_score, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (item.id, item.content, item.created_at, item.last_recalled_at,
             item.recall_count, item.arbitrary_importance, item.zone,
             json.dumps(item.metadata), embedding_blob, item.total_score, _time.time()),
        )
        conn.commit()

    def get(self, item_id: str) -> MemoryItem | None:
        conn = self._get_conn()
        cur = conn.execute(f"SELECT * FROM {self._table} WHERE id = ?", (item_id,))
        row = cur.fetchone()
        return self._row_to_item(row) if row else None

    def remove(self, item_id: str) -> bool:
        conn = self._get_conn()
        cur = conn.execute(f"DELETE FROM {self._table} WHERE id = ?", (item_id,))
        conn.commit()
        return cur.rowcount > 0

    def update(self, item: MemoryItem) -> None:
        import time as _time
        embedding_blob = None
        if item.embedding is not None:
            from stellar_memory.utils import serialize_embedding
            embedding_blob = serialize_embedding(item.embedding)
        conn = self._get_conn()
        conn.execute(
            f"UPDATE {self._table} SET content=?, last_recalled_at=?, recall_count=?, "
            "arbitrary_importance=?, zone=?, metadata=?, embedding=?, total_score=?, updated_at=? WHERE id=?",
            (item.content, item.last_recalled_at, item.recall_count,
             item.arbitrary_importance, item.zone, json.dumps(item.metadata),
             embedding_blob, item.total_score, _time.time(), item.id),
        )
        conn.commit()

    def search(self, query: str, limit: int = 5,
               query_embedding: list[float] | None = None) -> list[MemoryItem]:
        conn = self._get_conn()
        words = query.lower().split()
        if not words:
            return []
        if query_embedding is not None:
            # Phase 1: Pre-filter by keyword (limit * 5 candidates)
            candidate_limit = limit * 5
            conditions = " OR ".join(["LOWER(content) LIKE ?" for _ in words])
            params = [f"%{w}%" for w in words]
            cur = conn.execute(
                f"SELECT * FROM {self._table} WHERE {conditions} LIMIT ?",
                params + [candidate_limit],
            )
            candidates = [self._row_to_item(row) for row in cur.fetchall()]

            # Phase 1b: supplement with recent embedded items if not enough
            if len(candidates) < candidate_limit:
                existing_ids = {c.id for c in candidates}
                cur2 = conn.execute(
                    f"SELECT * FROM {self._table} WHERE embedding IS NOT NULL "
                    f"ORDER BY last_recalled_at DESC LIMIT ?",
                    (candidate_limit - len(candidates),),
                )
                for row in cur2.fetchall():
                    item = self._row_to_item(row)
                    if item.id not in existing_ids:
                        candidates.append(item)

            # Phase 2: Re-rank by hybrid score
            from stellar_memory.utils import cosine_similarity
            scored: list[tuple[float, MemoryItem]] = []
            for item in candidates:
                content_lower = item.content.lower()
                match_count = sum(1 for w in words if w in content_lower)
                keyword_score = match_count / len(words)
                semantic_score = 0.0
                if item.embedding is not None:
                    semantic_score = cosine_similarity(query_embedding, item.embedding)
                    score = 0.7 * semantic_score + 0.3 * keyword_score
                else:
                    score = keyword_score
                if score > 0:
                    scored.append((score, item))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [item for _, item in scored[:limit]]
        else:
            conditions = " OR ".join(["LOWER(content) LIKE ?" for _ in words])
            params = [f"%{w}%" for w in words]
            cur = conn.execute(
                f"SELECT * FROM {self._table} WHERE {conditions} LIMIT ?",
                params + [limit],
            )
            return [self._row_to_item(row) for row in cur.fetchall()]

    def get_all(self) -> list[MemoryItem]:
        conn = self._get_conn()
        cur = conn.execute(f"SELECT * FROM {self._table}")
        return [self._row_to_item(row) for row in cur.fetchall()]

    def count(self) -> int:
        conn = self._get_conn()
        cur = conn.execute(f"SELECT COUNT(*) FROM {self._table}")
        return cur.fetchone()[0]

    def get_lowest_score_item(self) -> MemoryItem | None:
        conn = self._get_conn()
        cur = conn.execute(
            f"SELECT * FROM {self._table} ORDER BY total_score ASC LIMIT 1"
        )
        row = cur.fetchone()
        return self._row_to_item(row) if row else None
