"""Tests for EventBus and StellarMemory event integration."""

import pytest

from stellar_memory.event_bus import EventBus
from stellar_memory.config import StellarConfig
from stellar_memory.stellar import StellarMemory


class TestEventBus:
    def test_on_and_emit(self):
        bus = EventBus()
        received = []
        bus.on("on_store", lambda item: received.append(item))
        bus.emit("on_store", "test_item")
        assert received == ["test_item"]

    def test_multiple_handlers(self):
        bus = EventBus()
        results = []
        bus.on("on_store", lambda item: results.append(f"a:{item}"))
        bus.on("on_store", lambda item: results.append(f"b:{item}"))
        bus.emit("on_store", "x")
        assert results == ["a:x", "b:x"]

    def test_off_removes_handler(self):
        bus = EventBus()
        received = []
        handler = lambda item: received.append(item)
        bus.on("on_store", handler)
        bus.off("on_store", handler)
        bus.emit("on_store", "test")
        assert received == []

    def test_handler_error_does_not_propagate(self):
        bus = EventBus()
        results = []

        def bad_handler(item):
            raise ValueError("boom")

        bus.on("on_store", bad_handler)
        bus.on("on_store", lambda item: results.append(item))
        bus.emit("on_store", "ok")
        assert results == ["ok"]

    def test_clear_specific_event(self):
        bus = EventBus()
        received = []
        bus.on("on_store", lambda item: received.append("store"))
        bus.on("on_recall", lambda items, q: received.append("recall"))
        bus.clear("on_store")
        bus.emit("on_store", "x")
        bus.emit("on_recall", [], "q")
        assert received == ["recall"]

    def test_clear_all(self):
        bus = EventBus()
        received = []
        bus.on("on_store", lambda item: received.append("s"))
        bus.on("on_recall", lambda items, q: received.append("r"))
        bus.clear()
        bus.emit("on_store", "x")
        bus.emit("on_recall", [], "q")
        assert received == []

    def test_invalid_event_raises(self):
        bus = EventBus()
        with pytest.raises(ValueError, match="Unknown event"):
            bus.on("invalid_event", lambda: None)

    def test_stellar_store_emits_on_store(self):
        config = StellarConfig(db_path=":memory:")
        mem = StellarMemory(config)
        received = []
        mem.events.on("on_store", lambda item: received.append(item.id))
        item = mem.store("test content")
        assert len(received) == 1
        assert received[0] == item.id

    def test_stellar_recall_emits_on_recall(self):
        config = StellarConfig(db_path=":memory:")
        mem = StellarMemory(config)
        mem.store("hello world")
        received = []
        mem.events.on("on_recall", lambda items, query: received.append(query))
        mem.recall("hello")
        assert received == ["hello"]

    def test_stellar_forget_emits_on_forget(self):
        config = StellarConfig(db_path=":memory:")
        mem = StellarMemory(config)
        item = mem.store("to forget")
        received = []
        mem.events.on("on_forget", lambda mid: received.append(mid))
        mem.forget(item.id)
        assert received == [item.id]
