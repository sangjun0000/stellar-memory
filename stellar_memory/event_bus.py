"""Event bus for memory lifecycle hooks."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Callable, Any

logger = logging.getLogger(__name__)

EventHandler = Callable[..., None]


class EventBus:
    """Publish-subscribe event system for memory lifecycle events."""

    EVENTS = (
        "on_store",
        "on_recall",
        "on_forget",
        "on_reorbit",
        "on_consolidate",
        "on_zone_change",
        "on_decay",
        "on_auto_forget",
        "on_summarize",
        "on_adaptive_decay",
    )

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def on(self, event: str, handler: EventHandler) -> None:
        """Register a handler for an event."""
        if event not in self.EVENTS:
            raise ValueError(f"Unknown event: {event}. Valid: {self.EVENTS}")
        self._handlers[event].append(handler)

    def off(self, event: str, handler: EventHandler) -> None:
        """Remove a handler for an event."""
        if handler in self._handlers[event]:
            self._handlers[event].remove(handler)

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Emit an event, calling all registered handlers."""
        for handler in self._handlers.get(event, []):
            try:
                handler(*args, **kwargs)
            except Exception:
                logger.exception(f"Error in event handler for {event}")

    def clear(self, event: str | None = None) -> None:
        """Clear handlers for a specific event or all events."""
        if event:
            self._handlers[event].clear()
        else:
            self._handlers.clear()
