"""Tests for OrbitManager - placement, eviction, reorbiting."""

import time
from stellar_memory.config import ZoneConfig, MemoryFunctionConfig
from stellar_memory.memory_function import MemoryFunction
from stellar_memory.models import MemoryItem
from stellar_memory.orbit_manager import OrbitManager
from stellar_memory.storage import StorageFactory


def make_item(id: str = "m1", score: float = 0.5, **kwargs) -> MemoryItem:
    defaults = dict(
        content="test", created_at=time.time(), last_recalled_at=time.time(),
        recall_count=0, arbitrary_importance=0.5, zone=-1, metadata={},
        total_score=score,
    )
    defaults.update(kwargs)
    return MemoryItem(id=id, **defaults)


SMALL_ZONES = [
    ZoneConfig(0, "core", max_slots=3, importance_min=0.8),
    ZoneConfig(1, "inner", max_slots=5, importance_min=0.5, importance_max=0.8),
    ZoneConfig(2, "outer", max_slots=None, importance_min=0.0, importance_max=0.5),
]


def make_mgr(zones=None):
    return OrbitManager(zones or SMALL_ZONES, StorageFactory(":memory:"))


class TestPlacement:
    def test_place_in_correct_zone(self):
        mgr = make_mgr()
        item = make_item("m1", score=0.9)
        mgr.place(item, 0, 0.9)
        assert item.zone == 0
        assert mgr.get_zone_count(0) == 1

    def test_place_updates_zone_field(self):
        mgr = make_mgr()
        item = make_item("m1")
        mgr.place(item, 1, 0.6)
        assert item.zone == 1


class TestEviction:
    def test_eviction_when_full(self):
        mgr = make_mgr()
        for i in range(3):
            mgr.place(make_item(f"m{i}", score=0.9 + i * 0.01), 0, 0.9 + i * 0.01)
        assert mgr.get_zone_count(0) == 3

        mgr.place(make_item("m_new", score=0.95), 0, 0.95)
        assert mgr.get_zone_count(0) == 3
        assert mgr.get_zone_count(1) >= 1

    def test_cascade_eviction(self):
        small = [
            ZoneConfig(0, "core", max_slots=1, importance_min=0.8),
            ZoneConfig(1, "inner", max_slots=1, importance_min=0.5, importance_max=0.8),
            ZoneConfig(2, "outer", max_slots=None, importance_min=0.0, importance_max=0.5),
        ]
        mgr = make_mgr(small)
        mgr.place(make_item("m1", score=0.9), 0, 0.9)
        mgr.place(make_item("m2", score=0.7), 1, 0.7)
        mgr.place(make_item("m3", score=0.95), 0, 0.95)
        assert mgr.get_zone_count(0) == 1
        total = sum(mgr.get_zone_count(z) for z in [0, 1, 2])
        assert total == 3


class TestReorbit:
    def test_reorbit_moves_stale_items(self):
        mgr = make_mgr()
        fn = MemoryFunction()
        now = time.time()
        item = make_item("m1", score=0.9, recall_count=100,
                         last_recalled_at=now, arbitrary_importance=1.0)
        mgr.place(item, 0, 0.9)
        assert item.zone == 0

        item.last_recalled_at = now - 1_000_000
        item.recall_count = 0
        item.arbitrary_importance = 0.0
        mgr.get_storage(0).update(item)

        result = mgr.reorbit_all(fn, now)
        assert result.moved >= 1
        updated = mgr.find_item("m1")
        assert updated.zone > 0
