"""Tests for EventLogger."""

import json
import os

import pytest

from stellar_memory.event_logger import EventLogger
from stellar_memory.event_bus import EventBus
from stellar_memory.config import StellarConfig, EventLoggerConfig
from stellar_memory.stellar import StellarMemory


class TestEventLogger:
    def test_creates_jsonl_file(self, tmp_path):
        log_path = str(tmp_path / "events.jsonl")
        el = EventLogger(log_path=log_path)
        el._log("test_event", key="value")
        assert os.path.exists(log_path)

    def test_store_event_logged(self, tmp_path):
        log_path = str(tmp_path / "events.jsonl")
        el = EventLogger(log_path=log_path)
        bus = EventBus()
        el.attach(bus)

        # Simulate store event with a mock item
        class MockItem:
            id = "test-id"
            content = "hello world"

        bus.emit("on_store", MockItem())
        entries = el.read_logs()
        assert len(entries) == 1
        assert entries[0]["event"] == "store"
        assert entries[0]["item_id"] == "test-id"

    def test_recall_event_logged(self, tmp_path):
        log_path = str(tmp_path / "events.jsonl")
        el = EventLogger(log_path=log_path)
        bus = EventBus()
        el.attach(bus)

        bus.emit("on_recall", ["item1", "item2"], "test query")
        entries = el.read_logs()
        assert len(entries) == 1
        assert entries[0]["event"] == "recall"
        assert entries[0]["query"] == "test query"
        assert entries[0]["result_count"] == 2

    def test_forget_event_logged(self, tmp_path):
        log_path = str(tmp_path / "events.jsonl")
        el = EventLogger(log_path=log_path)
        bus = EventBus()
        el.attach(bus)

        bus.emit("on_forget", "forgotten-id")
        entries = el.read_logs()
        assert len(entries) == 1
        assert entries[0]["event"] == "forget"
        assert entries[0]["item_id"] == "forgotten-id"

    def test_read_logs_limit(self, tmp_path):
        log_path = str(tmp_path / "events.jsonl")
        el = EventLogger(log_path=log_path)
        for i in range(10):
            el._log(f"event_{i}", index=i)
        entries = el.read_logs(limit=3)
        assert len(entries) == 3
        # Should be the last 3 entries
        assert entries[0]["event"] == "event_7"

    def test_log_rotation(self, tmp_path):
        log_path = str(tmp_path / "events.jsonl")
        # Very small max size to trigger rotation
        el = EventLogger(log_path=log_path, max_size_mb=0.0001)
        # Write enough to exceed max size
        for i in range(100):
            el._log("filler", data="x" * 100)
        rotated = tmp_path / "events.jsonl.1"
        assert rotated.exists()

    def test_stellar_auto_attach(self, tmp_path):
        db = str(tmp_path / "test.db")
        log_path = str(tmp_path / "events.jsonl")
        config = StellarConfig(
            db_path=db,
            event_logger=EventLoggerConfig(enabled=True, log_path=log_path),
        )
        mem = StellarMemory(config)
        assert mem._event_logger is not None
        # Store should trigger a log
        mem.store("logger test")
        entries = mem._event_logger.read_logs()
        assert len(entries) >= 1
        assert any(e["event"] == "store" for e in entries)

    def test_empty_log_returns_empty_list(self, tmp_path):
        log_path = str(tmp_path / "events.jsonl")
        el = EventLogger(log_path=log_path)
        entries = el.read_logs()
        assert entries == []
