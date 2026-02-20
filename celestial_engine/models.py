"""Celestial Memory Engine data models."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class CelestialItem:
    """Single memory item in the celestial memory system."""

    id: str
    content: str
    created_at: float
    last_recalled_at: float
    recall_count: int = 0
    arbitrary_importance: float = 0.5
    zone: int = -1
    metadata: dict = field(default_factory=dict)
    embedding: list[float] | None = None
    total_score: float = 0.0

    @classmethod
    def create(
        cls,
        content: str,
        importance: float = 0.5,
        metadata: dict | None = None,
    ) -> CelestialItem:
        now = time.time()
        return cls(
            id=str(uuid4()),
            content=content,
            created_at=now,
            last_recalled_at=now,
            recall_count=0,
            arbitrary_importance=max(0.0, min(1.0, importance)),
            zone=-1,
            metadata=metadata or {},
        )


@dataclass
class ScoreBreakdown:
    """Memory function score decomposition."""

    recall_score: float
    freshness_score: float
    arbitrary_score: float
    context_score: float
    total: float
    target_zone: int


@dataclass
class ZoneConfig:
    """Zone configuration."""

    zone_id: int
    name: str
    max_slots: int | None
    score_min: float
    score_max: float = float("inf")


@dataclass
class RebalanceResult:
    """Result of a rebalance operation."""

    moved: int = 0
    evicted: int = 0
    forgotten: int = 0
    total_items: int = 0
    duration_ms: float = 0.0


DEFAULT_ZONES = [
    ZoneConfig(zone_id=0, name="core", max_slots=20, score_min=0.50),
    ZoneConfig(zone_id=1, name="inner", max_slots=100, score_min=0.30, score_max=0.50),
    ZoneConfig(zone_id=2, name="outer", max_slots=1000, score_min=0.10, score_max=0.30),
    ZoneConfig(zone_id=3, name="belt", max_slots=None, score_min=-0.10, score_max=0.10),
    ZoneConfig(
        zone_id=4, name="cloud", max_slots=None, score_min=float("-inf"), score_max=-0.10
    ),
]
