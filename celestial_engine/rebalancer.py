"""Rebalancer - periodic memory rebalancing engine."""

from __future__ import annotations

import logging
import threading
import time

from celestial_engine.memory_function import CelestialMemoryFunction
from celestial_engine.models import RebalanceResult
from celestial_engine.zone_manager import ZoneManager

logger = logging.getLogger(__name__)


class Rebalancer:
    """Periodically recalculates scores and relocates memories across zones."""

    def __init__(
        self,
        memory_fn: CelestialMemoryFunction,
        zone_mgr: ZoneManager,
        interval_seconds: int = 300,
        auto_forget_seconds: float = 86400 * 90,
    ) -> None:
        self._fn = memory_fn
        self._zone_mgr = zone_mgr
        self._interval = interval_seconds
        self._auto_forget = auto_forget_seconds
        self._timer: threading.Timer | None = None
        self._running = False

    def rebalance(self, current_time: float | None = None) -> RebalanceResult:
        """Recalculate all scores, relocate, enforce capacity, forget stale."""
        now = current_time or time.time()
        start = time.time()

        all_items = self._zone_mgr.get_all_items()
        moves: list[tuple[str, int, int, float]] = []

        for item in all_items:
            breakdown = self._fn.calculate(item, now)
            item.total_score = breakdown.total
            if breakdown.target_zone != item.zone:
                moves.append((item.id, item.zone, breakdown.target_zone, breakdown.total))

        moves.sort(key=lambda x: x[3], reverse=True)

        moved = 0
        for item_id, from_z, to_z, score in moves:
            if self._zone_mgr.move(item_id, from_z, to_z, score):
                moved += 1

        evicted = self._zone_mgr.enforce_capacity()
        forgotten = self._zone_mgr.forget_stale(self._auto_forget, now)

        duration = (time.time() - start) * 1000
        return RebalanceResult(
            moved=moved,
            evicted=evicted,
            forgotten=forgotten,
            total_items=len(all_items),
            duration_ms=duration,
        )

    def start(self) -> None:
        """Start background rebalancing."""
        self._running = True
        self._schedule_next()

    def stop(self) -> None:
        """Stop background rebalancing."""
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _schedule_next(self) -> None:
        if not self._running:
            return
        self._timer = threading.Timer(self._interval, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self) -> None:
        try:
            result = self.rebalance()
            if result.moved > 0 or result.forgotten > 0:
                logger.info(
                    "Rebalance: moved=%d evicted=%d forgotten=%d (%.1fms)",
                    result.moved,
                    result.evicted,
                    result.forgotten,
                    result.duration_ms,
                )
        except Exception as e:
            logger.error("Rebalance failed: %s", e)
        finally:
            self._schedule_next()
