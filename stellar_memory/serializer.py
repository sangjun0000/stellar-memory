"""Memory serialization - export/import and snapshots."""

from __future__ import annotations

import base64
import json
import time

from stellar_memory.models import MemoryItem, MemorySnapshot
from stellar_memory.utils import serialize_embedding, deserialize_embedding


class MemorySerializer:
    def __init__(self, embedder_dim: int = 384):
        self._dim = embedder_dim

    def export_json(self, items: list[MemoryItem],
                    include_embeddings: bool = True) -> str:
        """Serialize all memories to a JSON string."""
        data = {
            "version": "0.3.0",
            "exported_at": time.time(),
            "count": len(items),
            "items": [self._item_to_dict(item, include_embeddings) for item in items],
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def import_json(self, json_str: str) -> list[MemoryItem]:
        """Restore memories from a JSON string."""
        data = json.loads(json_str)
        return [self._dict_to_item(d) for d in data["items"]]

    def _item_to_dict(self, item: MemoryItem, include_embedding: bool) -> dict:
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
        }
        if include_embedding and item.embedding is not None:
            blob = serialize_embedding(item.embedding)
            d["embedding_b64"] = base64.b64encode(blob).decode("ascii")
        return d

    def _dict_to_item(self, d: dict) -> MemoryItem:
        embedding = None
        if "embedding_b64" in d:
            blob = base64.b64decode(d["embedding_b64"])
            embedding = deserialize_embedding(blob)
        return MemoryItem(
            id=d["id"],
            content=d["content"],
            created_at=d["created_at"],
            last_recalled_at=d["last_recalled_at"],
            recall_count=d.get("recall_count", 0),
            arbitrary_importance=d.get("arbitrary_importance", 0.5),
            zone=d.get("zone", -1),
            metadata=d.get("metadata", {}),
            embedding=embedding,
            total_score=d.get("total_score", 0.0),
        )

    def snapshot(self, items: list[MemoryItem]) -> MemorySnapshot:
        """Create a point-in-time snapshot."""
        zone_dist: dict[int, int] = {}
        for item in items:
            zone_dist[item.zone] = zone_dist.get(item.zone, 0) + 1
        return MemorySnapshot(
            timestamp=time.time(),
            total_memories=len(items),
            zone_distribution=zone_dist,
            items=[self._item_to_dict(item, include_embedding=True) for item in items],
        )
