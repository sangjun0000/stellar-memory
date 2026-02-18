"""Blackhole prevention tests - ensures Core zone never overflows."""

import time
from stellar_memory import StellarMemory, StellarConfig, MemoryFunctionConfig
from stellar_memory.config import ZoneConfig


STRICT_CONFIG = StellarConfig(
    memory_function=MemoryFunctionConfig(
        w_recall=0.3, w_freshness=0.3, w_arbitrary=0.25, w_context=0.15,
        max_recall=1000, decay_alpha=0.0001, freshness_cap=-1.0,
    ),
    zones=[
        ZoneConfig(0, "core", max_slots=5, importance_min=0.8),
        ZoneConfig(1, "inner", max_slots=10, importance_min=0.5, importance_max=0.8),
        ZoneConfig(2, "outer", max_slots=50, importance_min=0.2, importance_max=0.5),
        ZoneConfig(3, "belt", max_slots=None, importance_min=0.0, importance_max=0.2),
        ZoneConfig(4, "cloud", max_slots=None, importance_min=float("-inf"), importance_max=0.0),
    ],
    db_path=":memory:",
    auto_start_scheduler=False,
)


def test_core_never_exceeds_max_slots():
    sm = StellarMemory(STRICT_CONFIG)
    for i in range(30):
        sm.store(f"important_memory_{i}", importance=1.0)
    sm.reorbit()
    stats = sm.stats()
    assert stats.zone_counts.get(0, 0) <= 5


def test_recall_log_convergence_prevents_accumulation():
    sm = StellarMemory(STRICT_CONFIG)
    items = []
    for i in range(20):
        items.append(sm.store(f"memory_{i}", importance=0.5))

    for _ in range(100):
        for item in items:
            sm.recall(item.content)

    sm.reorbit()
    stats = sm.stats()
    assert stats.zone_counts.get(0, 0) <= 5
    assert stats.total_memories == 20


def test_freshness_decay_moves_unreferenced_outward():
    sm = StellarMemory(STRICT_CONFIG)
    item = sm.store("will be forgotten", importance=0.6)
    initial_zone = item.zone

    stored = sm.get(item.id)
    stored.last_recalled_at = time.time() - 500_000
    storage = sm._orbit_mgr.get_storage(stored.zone)
    storage.update(stored)

    sm.reorbit()
    updated = sm.get(item.id)
    assert updated.zone > initial_zone


def test_mixed_usage_equilibrium():
    sm = StellarMemory(STRICT_CONFIG)
    hot = [sm.store(f"hot_{i}", importance=0.8) for i in range(5)]
    cold = [sm.store(f"cold_{i}", importance=0.3) for i in range(15)]

    for _ in range(30):
        for item in hot:
            sm.recall(item.content)

    now = time.time()
    for item in cold:
        stored = sm.get(item.id)
        if stored:
            stored.last_recalled_at = now - 100_000
            storage = sm._orbit_mgr.get_storage(stored.zone)
            storage.update(stored)

    sm.reorbit()
    stats = sm.stats()

    assert stats.zone_counts.get(0, 0) <= 5
    assert stats.total_memories == 20
