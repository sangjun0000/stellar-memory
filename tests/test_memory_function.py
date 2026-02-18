"""Tests for MemoryFunction - recall score, freshness, zone determination."""

import time
from stellar_memory.config import MemoryFunctionConfig
from stellar_memory.memory_function import MemoryFunction
from stellar_memory.models import MemoryItem


def make_item(**kwargs) -> MemoryItem:
    defaults = dict(
        id="test-1", content="test memory", created_at=time.time(),
        last_recalled_at=time.time(), recall_count=0,
        arbitrary_importance=0.5, zone=2, metadata={},
    )
    defaults.update(kwargs)
    return MemoryItem(**defaults)


class TestRecallScore:
    def test_zero_recall(self):
        fn = MemoryFunction()
        assert fn._recall_score(0) == 0.0

    def test_recall_increases_with_count(self):
        fn = MemoryFunction()
        scores = [fn._recall_score(i) for i in range(0, 101, 10)]
        for i in range(1, len(scores)):
            assert scores[i] >= scores[i - 1]

    def test_log_convergence_diminishing_returns(self):
        """Equal increments in count yield diminishing score gains."""
        fn = MemoryFunction()
        s0 = fn._recall_score(0)
        s100 = fn._recall_score(100)
        s200 = fn._recall_score(200)
        diff_1 = s100 - s0    # 0→100
        diff_2 = s200 - s100  # 100→200
        assert diff_2 < diff_1

    def test_clamped_at_one(self):
        fn = MemoryFunction()
        assert fn._recall_score(5000) <= 1.0
        assert fn._recall_score(100000) <= 1.0


class TestFreshnessScore:
    def test_freshness_max_at_recall(self):
        """Just recalled → F = 1.0 (normalized)."""
        fn = MemoryFunction()
        now = time.time()
        assert fn._freshness_score(now, now) == 1.0

    def test_freshness_decays_over_time(self):
        fn = MemoryFunction()
        now = time.time()
        f1 = fn._freshness_score(now - 100, now)
        f2 = fn._freshness_score(now - 1000, now)
        assert f1 > f2

    def test_freshness_bottoms_at_zero(self):
        cfg = MemoryFunctionConfig(freshness_cap=-1.0, decay_alpha=0.0001)
        fn = MemoryFunction(cfg)
        now = time.time()
        f = fn._freshness_score(now - 1_000_000, now)
        assert f == 0.0

    def test_freshness_range_zero_to_one(self):
        fn = MemoryFunction()
        now = time.time()
        for delta in [0, 10, 100, 1000, 100000, 1000000]:
            f = fn._freshness_score(now - delta, now)
            assert 0.0 <= f <= 1.0


class TestTotalImportance:
    def test_calculation_weighted_sum(self):
        cfg = MemoryFunctionConfig(
            w_recall=0.3, w_freshness=0.3, w_arbitrary=0.25, w_context=0.15
        )
        fn = MemoryFunction(cfg)
        now = time.time()
        item = make_item(recall_count=10, last_recalled_at=now, arbitrary_importance=0.8)
        breakdown = fn.calculate(item, now)
        expected = (0.3 * breakdown.recall_score
                    + 0.3 * 1.0  # freshness = 1.0 (just recalled, normalized)
                    + 0.25 * 0.8
                    + 0.15 * 0.0)
        assert abs(breakdown.total - expected) < 1e-9

    def test_zone_core_for_high_score(self):
        fn = MemoryFunction()
        now = time.time()
        item = make_item(recall_count=500, last_recalled_at=now, arbitrary_importance=1.0)
        breakdown = fn.calculate(item, now)
        # R≈0.9, F=1.0 (just recalled), A=1.0, C=0.0
        # Total ≈ 0.3*0.9 + 0.3*1.0 + 0.25*1.0 + 0.15*0 = 0.82
        assert breakdown.target_zone == 0  # Core

    def test_zone_belt_or_cloud_for_stale_item(self):
        """Stale item with zero importance should be in outer zones (belt/cloud)."""
        fn = MemoryFunction()
        now = time.time()
        item = make_item(
            recall_count=0, last_recalled_at=now - 1_000_000,
            arbitrary_importance=0.0,
        )
        breakdown = fn.calculate(item, now)
        assert breakdown.target_zone >= 3  # Belt or Cloud
