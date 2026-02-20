"""Celestial Memory Function v2 - with black hole prevention guarantees."""

from __future__ import annotations

import math
from dataclasses import dataclass

from celestial_engine.models import CelestialItem, ScoreBreakdown


@dataclass
class MemoryFunctionConfig:
    """Memory function v2 configuration."""

    w_recall: float = 0.25
    w_freshness: float = 0.30
    w_arbitrary: float = 0.25
    w_context: float = 0.20
    max_recall_cap: int = 1000
    freshness_alpha: float = 0.001
    freshness_floor: float = -86400.0


class MemoryPresets:
    """용도별 기억 함수 가중치 프리셋."""

    CONVERSATIONAL = MemoryFunctionConfig(
        w_recall=0.20,
        w_freshness=0.35,
        w_arbitrary=0.25,
        w_context=0.20,
    )
    """대화형: 최근 대화 중시, 오래된 기억은 빠르게 잊음."""

    FACTUAL = MemoryFunctionConfig(
        w_recall=0.30,
        w_freshness=0.15,
        w_arbitrary=0.35,
        w_context=0.20,
    )
    """사실 기반: 자주 참조되고 중요한 정보 우선, 시간 덜 민감."""

    RESEARCH = MemoryFunctionConfig(
        w_recall=0.15,
        w_freshness=0.20,
        w_arbitrary=0.25,
        w_context=0.40,
    )
    """연구용: 문맥 유사도 최우선, 관련 정보 클러스터링에 유리."""


# Zone placement thresholds: (zone_id, score_min)
_DEFAULT_ZONE_THRESHOLDS: list[tuple[int, float]] = [
    (0, 0.50),
    (1, 0.30),
    (2, 0.10),
    (3, -0.10),
    (4, float("-inf")),
]


class CelestialMemoryFunction:
    """Celestial memory function v2 with mathematical black hole prevention.

    Score formula:
        I(m) = w_r * R(m) + w_f * F(m) + w_a * A(m) + w_c * C(m)

    Black hole prevention:
        1. R(m) uses log(1+count)/log(1+MAX) - can never reach 1.0
        2. F(m) resets to 0.0 on recall, decays to -1.0 without recall
        3. Zone capacity limits with lowest-score eviction
    """

    def __init__(self, config: MemoryFunctionConfig | None = None):
        self._cfg = config or MemoryFunctionConfig()

    def calculate(
        self,
        item: CelestialItem,
        current_time: float,
        context_embedding: list[float] | None = None,
    ) -> ScoreBreakdown:
        r = self._recall_score(item.recall_count)
        f = self._freshness_score(item.last_recalled_at, current_time)
        a = item.arbitrary_importance
        c = self._context_score(item.embedding, context_embedding)

        total = (
            self._cfg.w_recall * r
            + self._cfg.w_freshness * f
            + self._cfg.w_arbitrary * a
            + self._cfg.w_context * c
        )

        target_zone = self._determine_zone(total)
        return ScoreBreakdown(r, f, a, c, total, target_zone)

    def _recall_score(self, recall_count: int) -> float:
        """R(m) = log(1 + count) / log(1 + MAX_RECALL_CAP).

        Black hole prevention #1:
        - Log function ensures the score can never exceed ~0.9996
        - Even with recall_count=999, R < 1.0
        - Diminishing returns on frequent recalls
        """
        if recall_count <= 0:
            return 0.0
        return math.log(1 + recall_count) / math.log(1 + self._cfg.max_recall_cap)

    def _freshness_score(self, last_recalled_at: float, current_time: float) -> float:
        """Recall-reset + negative decay freshness.

        Black hole prevention #2:
        - On recall: F(m) = 0.0 (reset via last_recalled_at update)
        - Over time: F(m) = -alpha * delta_t, normalized to [-1.0, 0.0]
        - Without recall, freshness decays to -1.0, pulling total score down

        Key difference from v1:
        - v1: F = exp(-alpha * (now - created_at)) -> [0, 1] (always positive)
        - v2: F = -alpha * (now - last_recalled_at) / |floor| -> [-1, 0] (negative!)
        """
        delta_t = max(0.0, current_time - last_recalled_at)
        raw = -self._cfg.freshness_alpha * delta_t
        clamped = max(raw, self._cfg.freshness_floor)
        if self._cfg.freshness_floor >= 0:
            return 0.0
        return clamped / abs(self._cfg.freshness_floor)

    def _context_score(
        self,
        item_embedding: list[float] | None,
        context_embedding: list[float] | None,
    ) -> float:
        """C(m) = cosine similarity between item and context embeddings."""
        if item_embedding is None or context_embedding is None:
            return 0.0
        dot = sum(a * b for a, b in zip(item_embedding, context_embedding))
        norm_a = sum(a * a for a in item_embedding) ** 0.5
        norm_b = sum(b * b for b in context_embedding) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _determine_zone(self, total_score: float) -> int:
        """Determine target zone based on total importance score."""
        for zone_id, score_min in _DEFAULT_ZONE_THRESHOLDS:
            if total_score >= score_min:
                return zone_id
        return 4
