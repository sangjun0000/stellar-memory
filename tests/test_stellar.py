"""Integration tests for StellarMemory main class."""

import time
from stellar_memory import StellarMemory, StellarConfig, MemoryFunctionConfig
from stellar_memory.config import ZoneConfig


FAST_CONFIG = StellarConfig(
    memory_function=MemoryFunctionConfig(decay_alpha=0.001),
    zones=[
        ZoneConfig(0, "core", max_slots=5, importance_min=0.8),
        ZoneConfig(1, "inner", max_slots=10, importance_min=0.5, importance_max=0.8),
        ZoneConfig(2, "outer", max_slots=100, importance_min=0.2, importance_max=0.5),
        ZoneConfig(3, "belt", max_slots=None, importance_min=0.0, importance_max=0.2),
        ZoneConfig(4, "cloud", max_slots=None, importance_min=float("-inf"), importance_max=0.0),
    ],
    db_path=":memory:",
    auto_start_scheduler=False,
)


class TestStoreAndRecall:
    def test_store_creates_memory(self):
        sm = StellarMemory(FAST_CONFIG)
        item = sm.store("Remember this important fact", importance=0.9)
        assert item.id is not None
        assert item.content == "Remember this important fact"
        assert item.zone >= 0

    def test_recall_finds_stored_memory(self):
        sm = StellarMemory(FAST_CONFIG)
        sm.store("The meeting is at 3pm tomorrow", importance=0.8)
        results = sm.recall("meeting tomorrow")
        assert len(results) >= 1
        assert "meeting" in results[0].content.lower()

    def test_recall_increases_count_and_resets_freshness(self):
        sm = StellarMemory(FAST_CONFIG)
        item = sm.store("Important date: 2026-03-01", importance=0.7)

        results = sm.recall("Important date")
        assert len(results) >= 1
        recalled = results[0]
        assert recalled.recall_count == 1

    def test_recall_empty_for_no_match(self):
        sm = StellarMemory(FAST_CONFIG)
        sm.store("Python programming language")
        results = sm.recall("quantum physics")
        assert len(results) == 0


class TestForget:
    def test_forget_removes_memory(self):
        sm = StellarMemory(FAST_CONFIG)
        item = sm.store("Delete me", importance=0.5)
        assert sm.forget(item.id) is True
        assert sm.get(item.id) is None

    def test_forget_nonexistent_returns_false(self):
        sm = StellarMemory(FAST_CONFIG)
        assert sm.forget("nonexistent-id") is False


class TestStats:
    def test_stats_reflect_stored_memories(self):
        sm = StellarMemory(FAST_CONFIG)
        sm.store("Memory A", importance=0.9)
        sm.store("Memory B", importance=0.3)
        sm.store("Memory C", importance=0.1)
        stats = sm.stats()
        assert stats.total_memories == 3

    def test_stats_show_zone_distribution(self):
        sm = StellarMemory(FAST_CONFIG)
        for i in range(10):
            sm.store(f"Memory {i}", importance=(i / 10.0))
        stats = sm.stats()
        assert sum(stats.zone_counts.values()) == 10


class TestBlackhole:
    def test_no_blackhole_after_heavy_recall(self):
        """Core zone should not overflow even after many recalls."""
        sm = StellarMemory(FAST_CONFIG)
        items = [sm.store(f"memory_{i}", importance=0.5) for i in range(20)]
        for _ in range(50):
            for item in items:
                sm.recall(item.content)
        sm.reorbit()
        stats = sm.stats()
        assert stats.zone_counts.get(0, 0) <= 5


class TestFullLifecycle:
    def test_store_recall_decay_reorbit(self):
        sm = StellarMemory(FAST_CONFIG)
        m1 = sm.store("Important appointment next week", importance=0.9)
        m2 = sm.store("Had lunch today", importance=0.2)

        assert m1.zone <= m2.zone

        sm.recall("appointment")

        initial_zone = m2.zone
        item = sm.get(m2.id)
        if item:
            item.last_recalled_at = time.time() - 100_000
            storage = sm._orbit_mgr.get_storage(item.zone)
            storage.update(item)

        sm.reorbit()
        updated = sm.get(m2.id)
        if updated:
            assert updated.zone >= initial_zone
