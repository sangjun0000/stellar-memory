"""CRDT-based memory sync manager (LWW-Register)."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.models import ChangeEvent

logger = logging.getLogger(__name__)


class MemorySyncManager:
    """Last-Write-Wins sync using CRDT semantics with vector clocks."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        # Vector clock for causal ordering
        self._clock: dict[str, int] = {}
        # LWW register: item_id -> (timestamp, agent_id)
        self._lww: dict[str, tuple[float, str]] = {}
        self._pending: list[ChangeEvent] = []
        self._server = None
        self._client = None

    def record_change(self, event_type: str, item_id: str,
                      payload: dict | None = None) -> ChangeEvent:
        from stellar_memory.models import ChangeEvent
        self._clock[self.agent_id] = self._clock.get(self.agent_id, 0) + 1
        ts = time.time()
        evt = ChangeEvent(
            event_type=event_type,
            item_id=item_id,
            agent_id=self.agent_id,
            timestamp=ts,
            vector_clock=dict(self._clock),
            payload=payload or {},
        )
        self._lww[item_id] = (ts, self.agent_id)
        self._pending.append(evt)
        return evt

    def should_accept(self, event: ChangeEvent) -> bool:
        """LWW conflict resolution: latest timestamp wins."""
        existing = self._lww.get(event.item_id)
        if existing is None:
            return True
        local_ts, _ = existing
        if event.timestamp > local_ts:
            return True
        if event.timestamp == local_ts:
            return event.agent_id > self.agent_id
        return False

    def apply_remote(self, event: ChangeEvent) -> bool:
        if self.should_accept(event):
            self._lww[event.item_id] = (event.timestamp, event.agent_id)
            # Merge vector clocks
            for agent, count in event.vector_clock.items():
                self._clock[agent] = max(
                    self._clock.get(agent, 0), count
                )
            return True
        return False

    def flush_pending(self) -> list[ChangeEvent]:
        events = list(self._pending)
        self._pending.clear()
        return events

    @property
    def vector_clock(self) -> dict[str, int]:
        return dict(self._clock)

    def start_server(self, host: str = "0.0.0.0",
                     port: int = 8765) -> None:
        """Start WebSocket server (non-blocking)."""
        try:
            from stellar_memory.sync.ws_server import WsServer
            self._server = WsServer(self, host, port)
            self._server.start()
            logger.info("Sync server started on %s:%d", host, port)
        except ImportError:
            logger.warning("websockets not installed – server disabled")

    def connect_remote(self, url: str) -> None:
        """Connect to a remote sync server."""
        try:
            from stellar_memory.sync.ws_client import WsClient
            self._client = WsClient(self, url)
            self._client.start()
            logger.info("Connected to remote sync: %s", url)
        except ImportError:
            logger.warning("websockets not installed – client disabled")

    def stop(self) -> None:
        if self._server:
            self._server.stop()
            self._server = None
        if self._client:
            self._client.stop()
            self._client = None
