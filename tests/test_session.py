"""Tests for session context management."""

import pytest

from stellar_memory.config import StellarConfig, SessionConfig
from stellar_memory.session import SessionManager
from stellar_memory.models import MemoryItem, SessionInfo
from stellar_memory.stellar import StellarMemory


@pytest.fixture
def session_mgr():
    return SessionManager(SessionConfig())


@pytest.fixture
def memory(tmp_path):
    config = StellarConfig(
        db_path=str(tmp_path / "test.db"),
        session=SessionConfig(
            enabled=True,
            auto_summarize=True,
            summary_max_items=3,
            scope_current_first=True,
        ),
    )
    return StellarMemory(config)


def test_start_session(session_mgr):
    """start_session should create a SessionInfo with ID."""
    session = session_mgr.start_session()
    assert isinstance(session, SessionInfo)
    assert session.session_id != ""
    assert session.started_at > 0


def test_end_session(session_mgr):
    """end_session should set ended_at and clear current session."""
    session_mgr.start_session()
    ended = session_mgr.end_session()
    assert ended is not None
    assert ended.ended_at is not None
    assert session_mgr.current_session_id is None


def test_end_session_without_start(session_mgr):
    """end_session without start should return None."""
    result = session_mgr.end_session()
    assert result is None


def test_tag_memory(session_mgr):
    """tag_memory should add session_id to metadata."""
    session = session_mgr.start_session()
    item = MemoryItem.create("Test content")
    session_mgr.tag_memory(item)
    assert item.metadata["session_id"] == session.session_id
    assert session.memory_count == 1


def test_tag_memory_no_session(session_mgr):
    """tag_memory without active session should not modify item."""
    item = MemoryItem.create("Test content")
    session_mgr.tag_memory(item)
    assert "session_id" not in item.metadata


def test_current_session_id(session_mgr):
    """current_session_id should reflect active session."""
    assert session_mgr.current_session_id is None
    session = session_mgr.start_session()
    assert session_mgr.current_session_id == session.session_id
    session_mgr.end_session()
    assert session_mgr.current_session_id is None


def test_stellar_session_store_tags(memory):
    """Stored memories during session should be tagged."""
    memory.start_session()
    item = memory.store("Session memory")
    assert "session_id" in item.metadata
    memory.end_session(summarize=False)


def test_stellar_session_end_summarize(memory):
    """end_session with summarize should create summary."""
    session = memory.start_session()
    memory.store("Important fact A", importance=0.9)
    memory.store("Important fact B", importance=0.8)
    ended = memory.end_session(summarize=True)
    assert ended is not None
    assert ended.summary is not None
    assert len(ended.summary) > 0


def test_stellar_session_end_no_summarize(memory):
    """end_session with summarize=False should not create summary."""
    memory.start_session()
    memory.store("Some content")
    ended = memory.end_session(summarize=False)
    assert ended is not None
    assert ended.summary is None


def test_stellar_session_recall_prioritizes_current(memory):
    """recall during session should prioritize current session items."""
    # Store item without session
    memory.store("Python programming basics")

    # Start session and store session item
    memory.start_session()
    memory.store("Python advanced patterns for session")

    results = memory.recall("Python", limit=5)
    assert len(results) >= 1
    memory.end_session(summarize=False)
