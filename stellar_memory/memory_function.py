"""Memory Function - calculates total importance score I(m) for each memory."""

from __future__ import annotations

import math

from stellar_memory.config import MemoryFunctionConfig, ZoneConfig, DEFAULT_ZONES
from stellar_memory.models import MemoryItem, ScoreBreakdown


class MemoryFunction:
    def __init__(self, config: MemoryFunctionConfig | None = None,
                 zones: list[ZoneConfig] | None = None):
        self._cfg = config or MemoryFunctionConfig()
        self._zones = sorted(zones or DEFAULT_ZONES,
                             key=lambda z: z.importance_min, reverse=True)

    def calculate(self, item: MemoryItem, current_time: float,
                  context_embedding: list[float] | None = None) -> ScoreBreakdown:
        r = self._recall_score(item.recall_count)
        f = self._freshness_score(item.last_recalled_at, current_time)
        a = item.arbitrary_importance
        c = self._context_score(item.embedding, context_embedding)
        e = self._emotion_score(item)

        total = (self._cfg.w_recall * r
                 + self._cfg.w_freshness * f
                 + self._cfg.w_arbitrary * a
                 + self._cfg.w_context * c
                 + self._cfg.w_emotion * e)

        target_zone = self._determine_zone(total)
        return ScoreBreakdown(r, f, a, c, total, target_zone, e)

    def _recall_score(self, recall_count: int) -> float:
        """R(m) = min(log(1 + count) / log(1 + MAX), 1.0)"""
        if recall_count <= 0:
            return 0.0
        raw = math.log(1 + recall_count) / math.log(1 + self._cfg.max_recall)
        return min(raw, 1.0)

    def _freshness_score(self, last_recalled_at: float, current_time: float) -> float:
        """
        F(m) normalized to [0, 1]:
        - Just recalled (delta_t=0): F = 1.0 (freshest)
        - Cap reached: F = 0.0 (stalest)

        Internal: raw = -alpha * delta_t, capped at freshness_cap
        Normalized: (raw - cap) / (0 - cap)
        """
        delta_t = current_time - last_recalled_at
        if delta_t < 0:
            delta_t = 0
        raw = -self._cfg.decay_alpha * delta_t
        capped = max(raw, self._cfg.freshness_cap)
        if self._cfg.freshness_cap >= 0:
            return 0.0
        return (capped - self._cfg.freshness_cap) / (0 - self._cfg.freshness_cap)

    def _context_score(self, item_embedding: list[float] | None,
                       context_embedding: list[float] | None) -> float:
        """Cosine similarity between item and context embeddings. Returns 0.0 if no embeddings."""
        if item_embedding is None or context_embedding is None:
            return 0.0
        from stellar_memory.utils import cosine_similarity
        return cosine_similarity(item_embedding, context_embedding)

    def _emotion_score(self, item: MemoryItem) -> float:
        """E(m) = emotion intensity. Returns 0.0 if no emotion."""
        if item.emotion is None:
            return 0.0
        return item.emotion.intensity

    def _determine_zone(self, total_score: float) -> int:
        """Determine target zone based on total importance score."""
        for zone in self._zones:
            if total_score >= zone.importance_min:
                return zone.zone_id
        return self._zones[-1].zone_id
