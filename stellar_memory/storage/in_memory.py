"""In-memory storage for Zone 0 (Core) and Zone 1 (Inner)."""

from __future__ import annotations

from stellar_memory.storage import ZoneStorage
from stellar_memory.models import MemoryItem


class InMemoryStorage(ZoneStorage):
    def __init__(self) -> None:
        self._items: dict[str, MemoryItem] = {}

    def store(self, item: MemoryItem) -> None:
        self._items[item.id] = item

    def get(self, item_id: str) -> MemoryItem | None:
        return self._items.get(item_id)

    def remove(self, item_id: str) -> bool:
        return self._items.pop(item_id, None) is not None

    def update(self, item: MemoryItem) -> None:
        if item.id in self._items:
            self._items[item.id] = item

    def search(self, query: str, limit: int = 5,
               query_embedding: list[float] | None = None) -> list[MemoryItem]:
        query_words = query.lower().split()
        if not query_words:
            return []
        scored: list[tuple[float, MemoryItem]] = []
        for item in self._items.values():
            content_lower = item.content.lower()
            match_count = sum(1 for w in query_words if w in content_lower)
            keyword_score = match_count / len(query_words)

            semantic_score = 0.0
            if query_embedding is not None and item.embedding is not None:
                from stellar_memory.utils import cosine_similarity
                semantic_score = cosine_similarity(query_embedding, item.embedding)

            if query_embedding is not None and item.embedding is not None:
                score = 0.7 * semantic_score + 0.3 * keyword_score
            else:
                score = keyword_score

            if score > 0:
                scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def get_all(self) -> list[MemoryItem]:
        return list(self._items.values())

    def count(self) -> int:
        return len(self._items)

    def get_lowest_score_item(self) -> MemoryItem | None:
        if not self._items:
            return None
        return min(self._items.values(), key=lambda x: x.total_score)
