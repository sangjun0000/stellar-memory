"""Tests for P6 sync module: MemorySyncManager, CRDT LWW."""

import time
import pytest

from stellar_memory.models import ChangeEvent
from stellar_memory.sync.sync_manager import MemorySyncManager


class TestMemorySyncManager:
    def test_record_change(self):
        mgr = MemorySyncManager("agent-A")
        evt = mgr.record_change("store", "item-1", {"content": "hello"})
        assert evt.event_type == "store"
        assert evt.item_id == "item-1"
        assert evt.agent_id == "agent-A"
        assert evt.timestamp > 0

    def test_pending_events(self):
        mgr = MemorySyncManager("agent-A")
        mgr.record_change("store", "item-1")
        mgr.record_change("update", "item-2")
        pending = mgr.flush_pending()
        assert len(pending) == 2
        assert mgr.flush_pending() == []

    def test_lww_accepts_newer(self):
        mgr = MemorySyncManager("agent-A")
        mgr.record_change("store", "item-1")
        time.sleep(0.01)

        remote = ChangeEvent(
            event_type="update",
            item_id="item-1",
            agent_id="agent-B",
            timestamp=time.time(),
        )
        assert mgr.should_accept(remote)

    def test_lww_rejects_older(self):
        mgr = MemorySyncManager("agent-A")
        old_ts = time.time() - 100
        remote = ChangeEvent(
            event_type="store",
            item_id="item-1",
            agent_id="agent-B",
            timestamp=old_ts,
        )
        mgr.record_change("store", "item-1")
        assert not mgr.should_accept(remote)

    def test_lww_tie_breaks_by_agent_id(self):
        mgr = MemorySyncManager("agent-A")
        ts = time.time()
        mgr._lww["item-1"] = (ts, "agent-A")

        # agent-B > agent-A alphabetically
        remote = ChangeEvent(
            event_type="update",
            item_id="item-1",
            agent_id="agent-B",
            timestamp=ts,
        )
        assert mgr.should_accept(remote)

        # agent-0 < agent-A alphabetically
        remote2 = ChangeEvent(
            event_type="update",
            item_id="item-1",
            agent_id="agent-0",
            timestamp=ts,
        )
        assert not mgr.should_accept(remote2)

    def test_apply_remote_updates_lww(self):
        mgr = MemorySyncManager("agent-A")
        remote = ChangeEvent(
            event_type="store",
            item_id="item-1",
            agent_id="agent-B",
            timestamp=time.time(),
        )
        assert mgr.apply_remote(remote)
        assert mgr._lww["item-1"][1] == "agent-B"

    def test_apply_remote_rejects(self):
        mgr = MemorySyncManager("agent-A")
        mgr.record_change("store", "item-1")
        old = ChangeEvent(
            event_type="update",
            item_id="item-1",
            agent_id="agent-B",
            timestamp=time.time() - 1000,
        )
        assert not mgr.apply_remote(old)

    def test_accepts_new_item(self):
        mgr = MemorySyncManager("agent-A")
        remote = ChangeEvent(
            event_type="store",
            item_id="new-item",
            agent_id="agent-B",
            timestamp=time.time(),
        )
        assert mgr.should_accept(remote)

    def test_multiple_items(self):
        mgr = MemorySyncManager("agent-A")
        mgr.record_change("store", "item-1")
        mgr.record_change("store", "item-2")
        mgr.record_change("update", "item-1")
        assert len(mgr._lww) == 2
        pending = mgr.flush_pending()
        assert len(pending) == 3


class TestChangeEvent:
    def test_to_dict(self):
        evt = ChangeEvent(
            event_type="store",
            item_id="m1",
            agent_id="a1",
            timestamp=12345.0,
            payload={"key": "val"},
        )
        d = evt.to_dict()
        assert d["event_type"] == "store"
        assert d["payload"]["key"] == "val"

    def test_from_dict(self):
        d = {
            "event_type": "update",
            "item_id": "m2",
            "agent_id": "a2",
            "timestamp": 99999.0,
            "payload": {},
        }
        evt = ChangeEvent.from_dict(d)
        assert evt.event_type == "update"
        assert evt.agent_id == "a2"

    def test_roundtrip(self):
        evt = ChangeEvent(
            event_type="remove",
            item_id="m3",
            agent_id="a3",
            timestamp=time.time(),
            payload={"reason": "expired"},
        )
        restored = ChangeEvent.from_dict(evt.to_dict())
        assert restored.event_type == evt.event_type
        assert restored.item_id == evt.item_id
        assert restored.payload == evt.payload

    def test_vector_clock_field(self):
        evt = ChangeEvent(
            event_type="store",
            item_id="m1",
            agent_id="a1",
            timestamp=100.0,
            vector_clock={"a1": 3, "a2": 1},
        )
        d = evt.to_dict()
        assert d["vector_clock"] == {"a1": 3, "a2": 1}
        restored = ChangeEvent.from_dict(d)
        assert restored.vector_clock == {"a1": 3, "a2": 1}

    def test_vector_clock_default_empty(self):
        evt = ChangeEvent(
            event_type="store", item_id="m1",
            agent_id="a1", timestamp=100.0,
        )
        assert evt.vector_clock == {}


class TestSyncManagerVectorClock:
    def test_record_change_increments_clock(self):
        mgr = MemorySyncManager("agent-A")
        evt1 = mgr.record_change("store", "item-1")
        assert evt1.vector_clock == {"agent-A": 1}
        evt2 = mgr.record_change("update", "item-2")
        assert evt2.vector_clock == {"agent-A": 2}

    def test_apply_remote_merges_clock(self):
        mgr = MemorySyncManager("agent-A")
        mgr.record_change("store", "item-1")  # clock: {agent-A: 1}
        remote = ChangeEvent(
            event_type="store", item_id="item-2",
            agent_id="agent-B", timestamp=time.time(),
            vector_clock={"agent-B": 5, "agent-A": 0},
        )
        mgr.apply_remote(remote)
        # Should take max of each agent
        assert mgr.vector_clock["agent-A"] == 1
        assert mgr.vector_clock["agent-B"] == 5

    def test_vector_clock_property(self):
        mgr = MemorySyncManager("agent-A")
        mgr.record_change("store", "item-1")
        vc = mgr.vector_clock
        assert vc == {"agent-A": 1}
        # Should return copy
        vc["agent-A"] = 999
        assert mgr.vector_clock["agent-A"] == 1
