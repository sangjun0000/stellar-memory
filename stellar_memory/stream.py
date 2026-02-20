"""Memory Stream - time-ordered memory retrieval and narrative generation."""

from __future__ import annotations

import datetime
import logging
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.stellar import StellarMemory

from stellar_memory.models import TimelineEntry

logger = logging.getLogger(__name__)


class MemoryStream:
    """Time-ordered memory stream with narrative generation."""

    def __init__(self, memory: StellarMemory):
        self._memory = memory

    def timeline(self, start=None, end=None,
                 limit: int = 100,
                 user_id: str | None = None) -> list[TimelineEntry]:
        """Retrieve memories in time order within a range.

        Args:
            start: Start time (Unix timestamp or "YYYY-MM-DD" string)
            end: End time (Unix timestamp or "YYYY-MM-DD" string)
            limit: Maximum entries to return
            user_id: Filter to specific user's memories
        """
        start_ts = self._parse_time(start) if start is not None else 0.0
        end_ts = self._parse_time(end) if end is not None else time.time()

        all_items = self._memory._orbit_mgr.get_all_items(user_id=user_id)
        filtered = [
            item for item in all_items
            if start_ts <= item.created_at <= end_ts
        ]
        filtered.sort(key=lambda x: x.created_at)
        filtered = filtered[:limit]

        return [
            TimelineEntry(
                timestamp=item.created_at,
                memory_id=item.id,
                content=item.content[:200],
                zone=item.zone,
                emotion=item.emotion,
                importance=item.arbitrary_importance,
            )
            for item in filtered
        ]

    def narrate(self, topic: str, limit: int = 10,
                user_id: str | None = None) -> str:
        """Generate a narrative from memories about a topic.

        Args:
            topic: Narrative topic/query
            limit: Number of memories to use
            user_id: Filter to specific user's memories
        """
        results = self._memory.recall(topic, limit=limit, user_id=user_id)
        if not results:
            return ""

        summarizer = self._memory._summarizer
        if summarizer is None:
            return "\n".join(f"- {item.content[:150]}" for item in results)

        memories_text = "\n".join(
            f"[{i+1}] {item.content[:200]}"
            for i, item in enumerate(results)
        )
        prompt = (
            f"Based on these memories about '{topic}', "
            f"create a brief narrative summary:\n\n{memories_text}\n\n"
            "Write a cohesive narrative in 2-3 sentences."
        )
        try:
            from stellar_memory.providers import ProviderRegistry
            llm = ProviderRegistry.create_llm(self._memory.config.llm)
            return llm.complete(prompt, max_tokens=200)
        except Exception:
            return "\n".join(f"- {item.content[:150]}" for item in results)

    def summarize_period(self, start, end) -> str:
        """Summarize memories within a time period."""
        entries = self.timeline(start, end)
        if not entries:
            return ""
        contents = [e.content for e in entries]
        combined = " | ".join(contents[:20])

        summarizer = self._memory._summarizer
        if summarizer and len(combined) > 100:
            return summarizer.summarize(combined) or combined[:200]
        return combined[:200]

    @staticmethod
    def _parse_time(value) -> float:
        """Convert time value to Unix timestamp."""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    dt = datetime.datetime.strptime(value, fmt)
                    return dt.timestamp()
                except ValueError:
                    continue
            raise ValueError(f"Cannot parse time: {value}")
        raise TypeError(f"Unsupported time type: {type(value)}")
