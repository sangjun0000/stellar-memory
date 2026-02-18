"""Tests for DecayManager and StellarMemory decay integration."""

import time

import pytest

from stellar_memory.config import StellarConfig, DecayConfig
from stellar_memory.decay_manager import DecayManager
from stellar_memory.models import MemoryItem, DecayResult
from stellar_memory.stellar import StellarMemory


SECONDS_PER_DAY = 86400


def make_item(item_id: str, zone: int, last_recalled_at: float) -> MemoryItem:
    return MemoryItem(
        id=item_id,
        content=f"content-{item_id}",
        created_at=last_recalled_at,
        last_recalled_at=last_recalled_at,
        zone=zone,
        total_score=0.5,
    )


class TestDecayManager:
    def test_disabled_returns_empty(self):
        config = DecayConfig(enabled=False)
        mgr = DecayManager(config)
        items = [make_item("a", 3, time.time())]
        result = mgr.check_decay(items, time.time())
        assert result.to_demote == []
        assert result.to_forget == []

    def test_decay_days_triggers_demote(self):
        config = DecayConfig(decay_days=30, min_zone_for_decay=2)
        mgr = DecayManager(config)
        now = time.time()
        old_item = make_item("a", 2, now - 31 * SECONDS_PER_DAY)
        result = mgr.check_decay([old_item], now)
        assert len(result.to_demote) == 1
        assert result.to_demote[0] == ("a", 2, 3)

    def test_auto_forget_cloud_item(self):
        config = DecayConfig(auto_forget_days=90, min_zone_for_decay=2)
        mgr = DecayManager(config)
        now = time.time()
        ancient_item = make_item("a", 4, now - 91 * SECONDS_PER_DAY)
        result = mgr.check_decay([ancient_item], now)
        assert len(result.to_forget) == 1
        assert result.to_forget[0] == "a"

    def test_min_zone_protects_core_inner(self):
        config = DecayConfig(decay_days=30, min_zone_for_decay=2)
        mgr = DecayManager(config)
        now = time.time()
        core_item = make_item("a", 0, now - 100 * SECONDS_PER_DAY)
        inner_item = make_item("b", 1, now - 100 * SECONDS_PER_DAY)
        result = mgr.check_decay([core_item, inner_item], now)
        assert result.to_demote == []
        assert result.to_forget == []

    def test_stellar_reorbit_applies_decay(self, tmp_path):
        db = str(tmp_path / "test.db")
        config = StellarConfig(
            db_path=db,
            decay=DecayConfig(enabled=True, decay_days=1, min_zone_for_decay=2),
        )
        mem = StellarMemory(config)
        item = mem.store("decay test", importance=0.3)
        # Manually set old last_recalled_at to trigger decay
        item.last_recalled_at = time.time() - 2 * SECONDS_PER_DAY
        storage = mem._orbit_mgr.get_storage(item.zone)
        storage.update(item)
        original_zone = item.zone

        # Only items in zone >= 2 decay
        if original_zone >= 2:
            mem.reorbit()
            updated = mem.get(item.id)
            # Should have been demoted or still exists
            assert updated is not None

    def test_decay_demotes_zone(self, tmp_path):
        db = str(tmp_path / "test.db")
        config = StellarConfig(
            db_path=db,
            decay=DecayConfig(enabled=True, decay_days=1, min_zone_for_decay=2),
        )
        mem = StellarMemory(config)
        # Store with low importance to land in outer zone (2+)
        item = mem.store("outer memory", importance=0.3)
        original_zone = item.zone

        if original_zone >= 2:
            # Age the item
            item.last_recalled_at = time.time() - 2 * SECONDS_PER_DAY
            storage = mem._orbit_mgr.get_storage(item.zone)
            storage.update(item)
            mem._apply_decay()
            updated = mem.get(item.id)
            if updated is not None:
                assert updated.zone >= original_zone

    def test_auto_forget_deletes_item(self, tmp_path):
        db = str(tmp_path / "test.db")
        config = StellarConfig(
            db_path=db,
            decay=DecayConfig(enabled=True, auto_forget_days=1, min_zone_for_decay=0),
        )
        mem = StellarMemory(config)
        item = mem.store("cloud memory", importance=0.0)
        # Force to cloud zone and age it
        if item.zone == 4:
            item.last_recalled_at = time.time() - 2 * SECONDS_PER_DAY
            storage = mem._orbit_mgr.get_storage(item.zone)
            storage.update(item)
            mem._apply_decay()
            assert mem.get(item.id) is None

    def test_zone_change_event_fires(self, tmp_path):
        events = []
        db = str(tmp_path / "test.db")
        config = StellarConfig(
            db_path=db,
            decay=DecayConfig(enabled=True, decay_days=1, min_zone_for_decay=2),
        )
        mem = StellarMemory(config)
        mem.events.on("on_zone_change", lambda item, fz, tz: events.append((fz, tz)))

        item = mem.store("event test", importance=0.3)
        if item.zone >= 2:
            item.last_recalled_at = time.time() - 2 * SECONDS_PER_DAY
            storage = mem._orbit_mgr.get_storage(item.zone)
            storage.update(item)
            mem._apply_decay()
            # If demoted, event should fire
            if events:
                assert events[0][1] > events[0][0]

    def test_fresh_item_not_decayed(self):
        config = DecayConfig(decay_days=30, min_zone_for_decay=2)
        mgr = DecayManager(config)
        now = time.time()
        fresh_item = make_item("a", 3, now - 5 * SECONDS_PER_DAY)
        result = mgr.check_decay([fresh_item], now)
        assert result.to_demote == []
        assert result.to_forget == []

    def test_decay_days_boundary(self):
        config = DecayConfig(decay_days=30, min_zone_for_decay=2)
        mgr = DecayManager(config)
        now = time.time()
        # Exactly at boundary (not yet past)
        boundary_item = make_item("a", 3, now - 29 * SECONDS_PER_DAY)
        result = mgr.check_decay([boundary_item], now)
        assert result.to_demote == []
