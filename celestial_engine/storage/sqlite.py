"""SQLite storage for Outer (Zone 2), Belt (Zone 3), and Cloud (Zone 4) zones."""

from __future__ import annotations

import json
import math
import sqlite3
import struct
import threading

from celestial_engine.models import CelestialItem
from celestial_engine.storage import ZoneStorage


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """두 벡터의 코사인 유사도 계산."""
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SqliteStorage(ZoneStorage):
    """SQLite-based persistent storage with WAL mode for cold zones."""

    def __init__(self, db_path: str, zone_id: int) -> None:
        self._db_path = db_path
        self._zone_id = zone_id
        self._table = f"memories_zone_{zone_id}"
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_table()

    def _create_table(self) -> None:
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._table} (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                created_at REAL NOT NULL,
                last_recalled_at REAL NOT NULL,
                recall_count INTEGER DEFAULT 0,
                arbitrary_importance REAL DEFAULT 0.5,
                zone INTEGER DEFAULT {self._zone_id},
                metadata TEXT DEFAULT '{{}}',
                embedding BLOB,
                total_score REAL DEFAULT 0.0
            )
        """)
        self._conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{self._table}_score "
            f"ON {self._table}(total_score)"
        )
        self._conn.commit()

    def store(self, item: CelestialItem) -> None:
        with self._lock:
            self._conn.execute(
                f"INSERT OR REPLACE INTO {self._table} "
                "(id, content, created_at, last_recalled_at, recall_count, "
                "arbitrary_importance, zone, metadata, embedding, total_score) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item.id,
                    item.content,
                    item.created_at,
                    item.last_recalled_at,
                    item.recall_count,
                    item.arbitrary_importance,
                    item.zone,
                    json.dumps(item.metadata),
                    _serialize_embedding(item.embedding),
                    item.total_score,
                ),
            )
            self._conn.commit()

    def get(self, item_id: str) -> CelestialItem | None:
        row = self._conn.execute(
            f"SELECT * FROM {self._table} WHERE id = ?", (item_id,)
        ).fetchone()
        return _row_to_item(row) if row else None

    def remove(self, item_id: str) -> bool:
        with self._lock:
            cursor = self._conn.execute(
                f"DELETE FROM {self._table} WHERE id = ?", (item_id,)
            )
            self._conn.commit()
            return cursor.rowcount > 0

    def update(self, item: CelestialItem) -> None:
        self.store(item)

    def search(
        self,
        query: str,
        limit: int = 5,
        query_embedding: list[float] | None = None,
    ) -> list[CelestialItem]:
        if query_embedding:
            with self._lock:
                rows = self._conn.execute(
                    f"SELECT * FROM {self._table} WHERE embedding IS NOT NULL"
                ).fetchall()
            scored = []
            for row in rows:
                item = _row_to_item(row)
                if item and item.embedding:
                    sim = _cosine_similarity(item.embedding, query_embedding)
                    scored.append((item, sim))
            scored.sort(key=lambda x: x[1], reverse=True)
            return [item for item, _ in scored[:limit]]

        q = f"%{query}%"
        rows = self._conn.execute(
            f"SELECT * FROM {self._table} WHERE content LIKE ? "
            f"ORDER BY total_score DESC LIMIT ?",
            (q, limit),
        ).fetchall()
        return [_row_to_item(r) for r in rows]

    def get_all(self) -> list[CelestialItem]:
        rows = self._conn.execute(f"SELECT * FROM {self._table}").fetchall()
        return [_row_to_item(r) for r in rows]

    def count(self) -> int:
        row = self._conn.execute(
            f"SELECT COUNT(*) FROM {self._table}"
        ).fetchone()
        return row[0] if row else 0

    def get_lowest_score_item(self) -> CelestialItem | None:
        row = self._conn.execute(
            f"SELECT * FROM {self._table} ORDER BY total_score ASC LIMIT 1"
        ).fetchone()
        return _row_to_item(row) if row else None

    def close(self) -> None:
        self._conn.close()


def _serialize_embedding(emb: list[float] | None) -> bytes | None:
    if emb is None:
        return None
    return struct.pack(f"{len(emb)}f", *emb)


def _deserialize_embedding(data: bytes | None) -> list[float] | None:
    if data is None:
        return None
    count = len(data) // 4
    return list(struct.unpack(f"{count}f", data))


def _row_to_item(row: tuple | None) -> CelestialItem | None:
    if row is None:
        return None
    return CelestialItem(
        id=row[0],
        content=row[1],
        created_at=row[2],
        last_recalled_at=row[3],
        recall_count=row[4],
        arbitrary_importance=row[5],
        zone=row[6],
        metadata=json.loads(row[7]) if row[7] else {},
        embedding=_deserialize_embedding(row[8]),
        total_score=row[9],
    )
