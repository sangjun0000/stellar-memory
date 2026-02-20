"""In-memory storage for Core (Zone 0) and Inner (Zone 1) zones."""

from __future__ import annotations

import math

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


class InMemoryStorage(ZoneStorage):
    """RAM-based storage for hot zones. Fast access, no persistence."""

    def __init__(self) -> None:
        self._items: dict[str, CelestialItem] = {}

    def store(self, item: CelestialItem) -> None:
        self._items[item.id] = item

    def get(self, item_id: str) -> CelestialItem | None:
        return self._items.get(item_id)

    def remove(self, item_id: str) -> bool:
        return self._items.pop(item_id, None) is not None

    def update(self, item: CelestialItem) -> None:
        self._items[item.id] = item

    def search(
        self,
        query: str,
        limit: int = 5,
        query_embedding: list[float] | None = None,
    ) -> list[CelestialItem]:
        if query_embedding:
            scored = []
            for item in self._items.values():
                if item.embedding:
                    sim = _cosine_similarity(item.embedding, query_embedding)
                    scored.append((item, sim))
            scored.sort(key=lambda x: x[1], reverse=True)
            return [item for item, _ in scored[:limit]]

        q = query.lower()
        matches = [i for i in self._items.values() if q in i.content.lower()]
        matches.sort(key=lambda i: i.total_score, reverse=True)
        return matches[:limit]

    def get_all(self) -> list[CelestialItem]:
        return list(self._items.values())

    def count(self) -> int:
        return len(self._items)

    def get_lowest_score_item(self) -> CelestialItem | None:
        if not self._items:
            return None
        return min(self._items.values(), key=lambda i: i.total_score)
