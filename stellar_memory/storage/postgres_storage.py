"""PostgreSQL + pgvector storage backend."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from stellar_memory.storage import StorageBackend

if TYPE_CHECKING:
    from stellar_memory.models import MemoryItem

logger = logging.getLogger(__name__)


class PostgresStorage(StorageBackend):
    """PostgreSQL storage backend with optional pgvector support."""

    def __init__(self, db_url: str, pool_size: int = 10):
        self._db_url = db_url
        self._pool_size = pool_size
        self._pool = None
        self._connected = False

    def connect(self) -> None:
        try:
            import asyncio
            asyncio.run(self._async_connect())
        except ImportError:
            raise ImportError(
                "asyncpg is required for PostgreSQL backend. "
                "Install with: pip install stellar-memory[postgres]"
            )

    async def _async_connect(self) -> None:
        import asyncpg
        self._pool = await asyncpg.create_pool(
            self._db_url, min_size=2, max_size=self._pool_size
        )
        await self._ensure_schema()
        self._connected = True

    async def _ensure_schema(self) -> None:
        async with self._pool.acquire() as conn:
            # Try to enable pgvector extension
            self._has_pgvector = False
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                self._has_pgvector = True
            except Exception:
                logger.info("pgvector extension not available, using BYTEA fallback")

            if self._has_pgvector:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS memories (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        created_at DOUBLE PRECISION NOT NULL,
                        last_recalled_at DOUBLE PRECISION NOT NULL,
                        recall_count INTEGER DEFAULT 0,
                        arbitrary_importance DOUBLE PRECISION DEFAULT 0.5,
                        zone INTEGER DEFAULT -1,
                        metadata JSONB DEFAULT '{}',
                        total_score DOUBLE PRECISION DEFAULT 0.0,
                        encrypted BOOLEAN DEFAULT FALSE,
                        source_type TEXT DEFAULT 'user',
                        source_url TEXT,
                        ingested_at DOUBLE PRECISION,
                        vector_clock JSONB DEFAULT '{}',
                        embedding vector(384),
                        user_id UUID REFERENCES users(id) ON DELETE CASCADE
                    )
                """)
            else:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS memories (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        created_at DOUBLE PRECISION NOT NULL,
                        last_recalled_at DOUBLE PRECISION NOT NULL,
                        recall_count INTEGER DEFAULT 0,
                        arbitrary_importance DOUBLE PRECISION DEFAULT 0.5,
                        zone INTEGER DEFAULT -1,
                        metadata JSONB DEFAULT '{}',
                        total_score DOUBLE PRECISION DEFAULT 0.0,
                        encrypted BOOLEAN DEFAULT FALSE,
                        source_type TEXT DEFAULT 'user',
                        source_url TEXT,
                        ingested_at DOUBLE PRECISION,
                        vector_clock JSONB DEFAULT '{}',
                        embedding BYTEA,
                        user_id UUID REFERENCES users(id) ON DELETE CASCADE
                    )
                """)

            # Add user_id column if table already exists without it
            try:
                await conn.execute("""
                    ALTER TABLE memories ADD COLUMN IF NOT EXISTS user_id UUID
                """)
            except Exception:
                pass

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_zone
                ON memories(zone)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_score
                ON memories(zone, total_score)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_importance
                ON memories(arbitrary_importance DESC)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_recalled
                ON memories(last_recalled_at DESC)
            """)
            # Multi-tenant indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_user_zone
                ON memories(user_id, zone)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_user_score
                ON memories(user_id, total_score DESC)
            """)
            # IVFFlat index for pgvector
            if self._has_pgvector:
                try:
                    await conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_memories_embedding
                        ON memories USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100)
                    """)
                except Exception:
                    pass  # IVFFlat needs data to build

    def disconnect(self) -> None:
        if self._pool:
            import asyncio
            asyncio.run(self._pool.close())
            self._connected = False

    def is_connected(self) -> bool:
        return self._connected and self._pool is not None

    def store(self, item: MemoryItem) -> None:
        import asyncio
        asyncio.run(self._async_store(item))

    async def _async_store(self, item: MemoryItem) -> None:
        # Prepare embedding based on backend type
        embedding_val = None
        if item.embedding is not None:
            if getattr(self, '_has_pgvector', False):
                # pgvector: pass as text '[1,2,3]'
                embedding_val = "[" + ",".join(str(v) for v in item.embedding) + "]"
            else:
                from stellar_memory.utils import serialize_embedding
                embedding_val = serialize_embedding(item.embedding)

        vector_clock_json = json.dumps(item.vector_clock or {})

        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO memories
                    (id, content, created_at, last_recalled_at, recall_count,
                     arbitrary_importance, zone, metadata, total_score,
                     encrypted, source_type, source_url, ingested_at,
                     vector_clock, embedding, user_id)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)
                ON CONFLICT (id) DO UPDATE SET
                    content=EXCLUDED.content, zone=EXCLUDED.zone,
                    total_score=EXCLUDED.total_score,
                    last_recalled_at=EXCLUDED.last_recalled_at,
                    recall_count=EXCLUDED.recall_count,
                    arbitrary_importance=EXCLUDED.arbitrary_importance,
                    metadata=EXCLUDED.metadata, embedding=EXCLUDED.embedding,
                    encrypted=EXCLUDED.encrypted,
                    vector_clock=EXCLUDED.vector_clock
            """, item.id, item.content, item.created_at, item.last_recalled_at,
                item.recall_count, item.arbitrary_importance, item.zone,
                json.dumps(item.metadata), item.total_score,
                item.encrypted, item.source_type, item.source_url,
                item.ingested_at, vector_clock_json, embedding_val,
                item.user_id)

    def get(self, item_id: str,
            user_id: str | None = None) -> MemoryItem | None:
        import asyncio
        return asyncio.run(self._async_get(item_id, user_id))

    async def _async_get(self, item_id: str,
                         user_id: str | None = None) -> MemoryItem | None:
        async with self._pool.acquire() as conn:
            if user_id:
                row = await conn.fetchrow(
                    "SELECT * FROM memories WHERE id = $1 AND user_id = $2",
                    item_id, user_id
                )
            else:
                row = await conn.fetchrow(
                    "SELECT * FROM memories WHERE id = $1", item_id
                )
            return self._row_to_item(row) if row else None

    def remove(self, item_id: str,
               user_id: str | None = None) -> bool:
        import asyncio
        return asyncio.run(self._async_remove(item_id, user_id))

    async def _async_remove(self, item_id: str,
                            user_id: str | None = None) -> bool:
        async with self._pool.acquire() as conn:
            if user_id:
                result = await conn.execute(
                    "DELETE FROM memories WHERE id = $1 AND user_id = $2",
                    item_id, user_id
                )
            else:
                result = await conn.execute(
                    "DELETE FROM memories WHERE id = $1", item_id
                )
            return result.endswith("1")

    def update(self, item: MemoryItem) -> None:
        self.store(item)

    def search(self, query: str, limit: int = 5,
               query_embedding: list[float] | None = None,
               zone: int | None = None,
               user_id: str | None = None) -> list[MemoryItem]:
        import asyncio
        return asyncio.run(self._async_search(query, limit, query_embedding,
                                              zone, user_id))

    async def _async_search(self, query: str, limit: int,
                            query_embedding: list[float] | None,
                            zone: int | None,
                            user_id: str | None = None) -> list[MemoryItem]:
        async with self._pool.acquire() as conn:
            # Build WHERE clauses
            conditions = []
            params = []
            idx = 1

            if user_id:
                conditions.append(f"user_id = ${idx}")
                params.append(user_id)
                idx += 1

            if query_embedding and getattr(self, '_has_pgvector', False):
                vec_str = "[" + ",".join(str(v) for v in query_embedding) + "]"
                vec_param_idx = idx
                params.append(vec_str)
                idx += 1

                if zone is not None:
                    conditions.append(f"zone = ${idx}")
                    params.append(zone)
                    idx += 1

                where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
                params.append(limit)
                rows = await conn.fetch(
                    f"SELECT *, embedding <=> ${vec_param_idx}::vector AS distance "
                    f"FROM memories {where} "
                    f"ORDER BY distance ASC LIMIT ${idx}",
                    *params
                )
            else:
                if zone is not None:
                    conditions.append(f"zone = ${idx}")
                    params.append(zone)
                    idx += 1

                conditions.append(f"LOWER(content) LIKE ${idx}")
                params.append(f"%{query.lower()}%")
                idx += 1

                where = f"WHERE {' AND '.join(conditions)}"
                params.append(limit)
                rows = await conn.fetch(
                    f"SELECT * FROM memories {where} "
                    f"ORDER BY total_score DESC LIMIT ${idx}",
                    *params
                )
            return [self._row_to_item(r) for r in rows]

    def get_all(self, zone: int | None = None,
                user_id: str | None = None) -> list[MemoryItem]:
        import asyncio
        return asyncio.run(self._async_get_all(zone, user_id))

    async def _async_get_all(self, zone: int | None,
                             user_id: str | None = None) -> list[MemoryItem]:
        async with self._pool.acquire() as conn:
            conditions = []
            params = []
            idx = 1

            if user_id:
                conditions.append(f"user_id = ${idx}")
                params.append(user_id)
                idx += 1
            if zone is not None:
                conditions.append(f"zone = ${idx}")
                params.append(zone)
                idx += 1

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            rows = await conn.fetch(
                f"SELECT * FROM memories {where}", *params
            )
            return [self._row_to_item(r) for r in rows]

    def count(self, zone: int | None = None,
              user_id: str | None = None) -> int:
        import asyncio
        return asyncio.run(self._async_count(zone, user_id))

    async def _async_count(self, zone: int | None,
                           user_id: str | None = None) -> int:
        async with self._pool.acquire() as conn:
            conditions = []
            params = []
            idx = 1

            if user_id:
                conditions.append(f"user_id = ${idx}")
                params.append(user_id)
                idx += 1
            if zone is not None:
                conditions.append(f"zone = ${idx}")
                params.append(zone)
                idx += 1

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            row = await conn.fetchrow(
                f"SELECT COUNT(*) FROM memories {where}", *params
            )
            return row[0]

    def get_lowest_score_item(self, zone: int) -> MemoryItem | None:
        import asyncio
        return asyncio.run(self._async_lowest(zone))

    async def _async_lowest(self, zone: int) -> MemoryItem | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM memories WHERE zone = $1 "
                "ORDER BY total_score ASC LIMIT 1", zone
            )
            return self._row_to_item(row) if row else None

    def _row_to_item(self, row) -> MemoryItem:
        from stellar_memory.models import MemoryItem
        embedding = None
        if row.get("embedding"):
            from stellar_memory.utils import deserialize_embedding
            embedding = deserialize_embedding(row["embedding"])
        user_id_val = row.get("user_id")
        return MemoryItem(
            id=row["id"],
            content=row["content"],
            created_at=row["created_at"],
            last_recalled_at=row["last_recalled_at"],
            recall_count=row["recall_count"],
            arbitrary_importance=row["arbitrary_importance"],
            zone=row["zone"],
            metadata=json.loads(row["metadata"]) if isinstance(row["metadata"], str) else (row["metadata"] or {}),
            embedding=embedding,
            total_score=row["total_score"],
            encrypted=row.get("encrypted", False),
            source_type=row.get("source_type", "user"),
            source_url=row.get("source_url"),
            ingested_at=row.get("ingested_at"),
            user_id=str(user_id_val) if user_id_val else None,
        )
