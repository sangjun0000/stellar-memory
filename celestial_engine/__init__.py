"""Celestial Memory Engine - Human-like memory for AI with black hole prevention.

Usage:
    from celestial_engine import CelestialMemory

    memory = CelestialMemory()
    memory.store("Python was created in 1991", importance=0.8)
    results = memory.recall("Python history")
"""

from __future__ import annotations

import logging
import time

from celestial_engine.importance import (
    DefaultEvaluator,
    ImportanceEvaluator,
    LLMEvaluator,
    RuleBasedEvaluator,
)
from celestial_engine.auto_memory import AutoMemory
from celestial_engine.memory_function import (
    CelestialMemoryFunction,
    MemoryFunctionConfig,
    MemoryPresets,
)
from celestial_engine.middleware import MemoryMiddleware
from celestial_engine.models import (
    CelestialItem,
    DEFAULT_ZONES,
    RebalanceResult,
    ScoreBreakdown,
    ZoneConfig,
)
from celestial_engine.rebalancer import Rebalancer
from celestial_engine.zone_manager import ZoneManager

logger = logging.getLogger(__name__)

__version__ = "2.0.0"

__all__ = [
    "CelestialMemory",
    "CelestialItem",
    "CelestialMemoryFunction",
    "MemoryFunctionConfig",
    "MemoryPresets",
    "MemoryMiddleware",
    "AutoMemory",
    "ZoneConfig",
    "ScoreBreakdown",
    "RebalanceResult",
    "DEFAULT_ZONES",
    "ImportanceEvaluator",
    "DefaultEvaluator",
    "RuleBasedEvaluator",
    "LLMEvaluator",
    "ZoneManager",
    "Rebalancer",
]


class CelestialMemory:
    """Celestial Memory Engine - public facade.

    A human-like memory system inspired by the solar system structure.
    Important memories orbit close to the sun (Core zone),
    while less important ones drift to outer orbits.

    Args:
        db_path: SQLite database path for persistent zones.
        zones: Custom zone configurations. Defaults to 5 standard zones.
        memory_fn_config: Memory function weight/parameter configuration.
        evaluator: Importance evaluator for auto-scoring. Defaults to DefaultEvaluator.
        rebalance_interval: Seconds between automatic rebalances.
        auto_forget_days: Days before Cloud zone items are deleted.
        embed_fn: Optional embedding function ``(text: str) -> list[float]``.
    """

    def __init__(
        self,
        db_path: str = "celestial_memory.db",
        zones: list[ZoneConfig] | None = None,
        memory_fn_config: MemoryFunctionConfig | None = None,
        evaluator: ImportanceEvaluator | None = None,
        rebalance_interval: int = 300,
        auto_forget_days: int = 90,
        embed_fn=None,
    ) -> None:
        self._fn = CelestialMemoryFunction(memory_fn_config)
        self._zone_mgr = ZoneManager(zones, db_path)
        self._evaluator = evaluator or DefaultEvaluator()
        self._embed_fn = embed_fn
        self._rebalancer = Rebalancer(
            self._fn,
            self._zone_mgr,
            interval_seconds=rebalance_interval,
            auto_forget_seconds=auto_forget_days * 86400,
        )
        self._rebalancer.start()

    def store(
        self,
        content: str,
        importance: float | None = None,
        metadata: dict | None = None,
    ) -> CelestialItem:
        """Store a memory.

        If importance is None, the evaluator auto-scores it.
        Returns the stored CelestialItem with zone assignment.
        """
        if importance is None:
            importance = self._evaluator.evaluate(content)

        item = CelestialItem.create(content, importance, metadata)

        if self._embed_fn:
            item.embedding = self._embed_fn(content)

        now = item.created_at
        breakdown = self._fn.calculate(item, now)
        self._zone_mgr.place(item, breakdown.target_zone, breakdown.total)
        return item

    def recall(self, query: str, limit: int = 5) -> list[CelestialItem]:
        """Recall memories matching query.

        Updates recall_count and last_recalled_at for returned items,
        triggering freshness reset (the core innovation of v2).
        """
        now = time.time()
        query_embedding = self._embed_fn(query) if self._embed_fn else None
        results = self._zone_mgr.search(query, limit, query_embedding)

        for item in results:
            item.recall_count += 1
            item.last_recalled_at = now
            breakdown = self._fn.calculate(item, now, query_embedding)
            if breakdown.target_zone != item.zone:
                self._zone_mgr.move(
                    item.id, item.zone, breakdown.target_zone, breakdown.total
                )
            else:
                item.total_score = breakdown.total
                self._zone_mgr._storages[item.zone].update(item)

        return results

    def rebalance(self) -> RebalanceResult:
        """Manually trigger a rebalance cycle."""
        return self._rebalancer.rebalance()

    def stats(self) -> dict:
        """Return zone statistics."""
        zone_stats = self._zone_mgr.stats()
        return {
            "zones": {
                zid: {"count": count, "capacity": cap}
                for zid, (count, cap) in zone_stats.items()
            },
            "total": sum(count for count, _ in zone_stats.values()),
        }

    def close(self) -> None:
        """Stop the rebalancer and release resources."""
        self._rebalancer.stop()
