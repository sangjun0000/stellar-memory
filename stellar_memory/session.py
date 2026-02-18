"""Session context manager for memory scoping."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
from uuid import uuid4

from stellar_memory.models import MemoryItem, SessionInfo

if TYPE_CHECKING:
    from stellar_memory.config import SessionConfig


class SessionManager:
    def __init__(self, config: SessionConfig):
        self._config = config
        self._current_session: SessionInfo | None = None

    @property
    def current_session_id(self) -> str | None:
        return self._current_session.session_id if self._current_session else None

    def start_session(self) -> SessionInfo:
        session_id = str(uuid4())
        self._current_session = SessionInfo(
            session_id=session_id,
            started_at=time.time(),
        )
        return self._current_session

    def end_session(self) -> SessionInfo | None:
        if self._current_session is None:
            return None
        self._current_session.ended_at = time.time()
        ended = self._current_session
        self._current_session = None
        return ended

    def tag_memory(self, item: MemoryItem) -> None:
        """Tag a memory item with the current session ID."""
        if self._current_session:
            item.metadata["session_id"] = self._current_session.session_id
            self._current_session.memory_count += 1
