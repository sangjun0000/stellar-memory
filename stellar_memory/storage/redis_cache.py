"""Redis cache layer for Core/Inner zone memories."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.models import MemoryItem

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis-based read cache for frequently accessed memories."""

    def __init__(self, redis_url: str, ttl: int = 300,
                 cached_zones: tuple = (0, 1)):
        self._url = redis_url
        self._ttl = ttl
        self._cached_zones = cached_zones
        self._client = None
        self._connected = False

    def connect(self) -> None:
        try:
            import redis as redis_lib
            self._client = redis_lib.from_url(
                self._url, decode_responses=False
            )
            self._client.ping()
            self._connected = True
        except ImportError:
            raise ImportError(
                "redis is required for Redis cache. "
                "Install with: pip install stellar-memory[redis]"
            )
        except Exception as e:
            logger.warning("Redis connection failed: %s", e)
            self._connected = False

    def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._connected = False

    def is_connected(self) -> bool:
        return self._connected and self._client is not None

    def get(self, item_id: str) -> MemoryItem | None:
        if not self._client:
            return None
        try:
            data = self._client.get(f"sm:{item_id}")
            if data:
                return self._deserialize(data)
        except Exception:
            pass
        return None

    def set(self, item: MemoryItem) -> None:
        if not self._client or item.zone not in self._cached_zones:
            return
        try:
            self._client.setex(
                f"sm:{item.id}", self._ttl, self._serialize(item)
            )
        except Exception:
            pass

    def invalidate(self, item_id: str) -> None:
        if self._client:
            try:
                self._client.delete(f"sm:{item_id}")
            except Exception:
                pass

    def invalidate_zone(self, zone: int) -> None:
        """Invalidate all cached items in a zone (scan-based)."""
        if not self._client:
            return
        try:
            cursor = 0
            while True:
                cursor, keys = self._client.scan(
                    cursor, match="sm:*", count=100
                )
                for key in keys:
                    data = self._client.get(key)
                    if data:
                        try:
                            d = json.loads(data)
                            if d.get("zone") == zone:
                                self._client.delete(key)
                        except (json.JSONDecodeError, TypeError):
                            pass
                if cursor == 0:
                    break
        except Exception:
            pass

    def _serialize(self, item: MemoryItem) -> bytes:
        d = {
            "id": item.id,
            "content": item.content,
            "created_at": item.created_at,
            "last_recalled_at": item.last_recalled_at,
            "recall_count": item.recall_count,
            "arbitrary_importance": item.arbitrary_importance,
            "zone": item.zone,
            "metadata": item.metadata,
            "total_score": item.total_score,
            "encrypted": item.encrypted,
            "source_type": item.source_type,
            "source_url": item.source_url,
            "ingested_at": item.ingested_at,
        }
        return json.dumps(d).encode()

    def _deserialize(self, data: bytes) -> MemoryItem:
        from stellar_memory.models import MemoryItem
        d = json.loads(data)
        return MemoryItem(
            id=d["id"],
            content=d["content"],
            created_at=d["created_at"],
            last_recalled_at=d["last_recalled_at"],
            recall_count=d.get("recall_count", 0),
            arbitrary_importance=d.get("arbitrary_importance", 0.5),
            zone=d.get("zone", -1),
            metadata=d.get("metadata", {}),
            total_score=d.get("total_score", 0.0),
            encrypted=d.get("encrypted", False),
            source_type=d.get("source_type", "user"),
            source_url=d.get("source_url"),
            ingested_at=d.get("ingested_at"),
        )
