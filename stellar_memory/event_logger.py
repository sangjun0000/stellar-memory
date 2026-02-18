"""Persistent event logger for memory activity audit trail."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from stellar_memory.event_bus import EventBus

logger = logging.getLogger(__name__)


class EventLogger:
    """Logs memory events to a JSONL file."""

    def __init__(self, log_path: str = "stellar_events.jsonl",
                 max_size_mb: float = 10.0):
        self._log_path = Path(log_path)
        self._max_size = int(max_size_mb * 1024 * 1024)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def attach(self, bus: EventBus) -> None:
        """Register handlers for all events on the bus."""
        bus.on("on_store", lambda item: self._log("store", item_id=item.id,
               content_preview=item.content[:80]))
        bus.on("on_recall", lambda items, query: self._log("recall",
               query=query, result_count=len(items)))
        bus.on("on_forget", lambda mid: self._log("forget", item_id=mid))
        bus.on("on_reorbit", lambda result: self._log("reorbit",
               moved=result.moved, evicted=result.evicted))
        bus.on("on_consolidate", lambda existing, new: self._log("consolidate",
               existing_id=existing.id, new_id=new.id))
        bus.on("on_zone_change", lambda item, fz, tz: self._log("zone_change",
               item_id=item.id, from_zone=fz, to_zone=tz))

    def _log(self, event_type: str, **kwargs) -> None:
        """Write a single event line to the log file."""
        self._rotate_if_needed()
        entry = {
            "timestamp": time.time(),
            "event": event_type,
            **kwargs,
        }
        with open(self._log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _rotate_if_needed(self) -> None:
        """Rotate log file if it exceeds max size."""
        if not self._log_path.exists():
            return
        if self._log_path.stat().st_size >= self._max_size:
            rotated = self._log_path.with_suffix(".jsonl.1")
            if rotated.exists():
                rotated.unlink()
            self._log_path.rename(rotated)

    def read_logs(self, limit: int = 100) -> list[dict]:
        """Read recent log entries."""
        if not self._log_path.exists():
            return []
        lines = self._log_path.read_text().strip().split("\n")
        entries = []
        for line in lines[-limit:]:
            if line:
                entries.append(json.loads(line))
        return entries
