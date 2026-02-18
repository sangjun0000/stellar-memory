"""Reorbit Scheduler - periodically recalculates and redistributes memories."""

from __future__ import annotations

import logging
import threading
import time

from stellar_memory.memory_function import MemoryFunction
from stellar_memory.orbit_manager import OrbitManager

logger = logging.getLogger(__name__)


class ReorbitScheduler:
    def __init__(self, orbit_mgr: OrbitManager, memory_fn: MemoryFunction,
                 interval: int = 300):
        self._orbit_mgr = orbit_mgr
        self._memory_fn = memory_fn
        self._interval = interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"Reorbit scheduler started (interval={self._interval}s)")

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("Reorbit scheduler stopped")

    def trigger_now(self) -> None:
        result = self._orbit_mgr.reorbit_all(self._memory_fn, time.time())
        logger.info(f"Manual reorbit: moved={result.moved}, evicted={result.evicted}, "
                     f"total={result.total_items}, duration={result.duration:.3f}s")

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            self._stop_event.wait(timeout=self._interval)
            if self._stop_event.is_set():
                break
            try:
                result = self._orbit_mgr.reorbit_all(self._memory_fn, time.time())
                logger.info(f"Reorbit: moved={result.moved}, evicted={result.evicted}, "
                             f"total={result.total_items}, duration={result.duration:.3f}s")
            except Exception:
                logger.exception("Error during reorbit cycle")
