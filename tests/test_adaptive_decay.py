"""Tests for P5-F4: Adaptive Decay / Importance-Based Forgetting."""

from __future__ import annotations

import time

import pytest

from stellar_memory.adaptive_decay import AdaptiveDecayManager, SECONDS_PER_DAY
from stellar_memory.decay_manager import DecayManager
from stellar_memory.config import DecayConfig, AdaptiveDecayConfig
from stellar_memory.models import MemoryItem


def _make_item(importance: float = 0.5, zone: int = 2,
               recalled_days_ago: float = 0) -> MemoryItem:
    now = time.time()
    return MemoryItem(
        id="test-id",
        content="test content",
        created_at=now - 100 * SECONDS_PER_DAY,
        last_recalled_at=now - recalled_days_ago * SECONDS_PER_DAY,
        recall_count=5,
        arbitrary_importance=importance,
        zone=zone,
    )


class TestEffectiveDecayDays:
    def test_high_importance_extends_decay(self):
        config = DecayConfig(
            decay_days=30, adaptive=AdaptiveDecayConfig(enabled=True)
        )
        mgr = AdaptiveDecayManager(config)
        item = _make_item(importance=0.9, zone=0)
        days = mgr.effective_decay_days(item)
        # zone=0 → zone_factor not applied (item.zone > 0 is False)
        # 30 * (0.5 + 0.9 * 1.0) = 30 * 1.4 = 42
        assert days == pytest.approx(42.0)

    def test_low_importance_shortens_decay(self):
        config = DecayConfig(
            decay_days=30, adaptive=AdaptiveDecayConfig(enabled=True)
        )
        mgr = AdaptiveDecayManager(config)
        item = _make_item(importance=0.1, zone=0)
        days = mgr.effective_decay_days(item)
        # zone=0 → no zone_factor: 30 * (0.5 + 0.1) = 18
        assert days == pytest.approx(18.0)

    def test_zero_importance(self):
        config = DecayConfig(
            decay_days=30, adaptive=AdaptiveDecayConfig(enabled=True)
        )
        mgr = AdaptiveDecayManager(config)
        item = _make_item(importance=0.0, zone=0)
        days = mgr.effective_decay_days(item)
        # zone=0 → no zone_factor: 30 * 0.5 = 15
        assert days == pytest.approx(15.0)

    def test_zone_factor_disabled(self):
        config = DecayConfig(
            decay_days=30,
            adaptive=AdaptiveDecayConfig(enabled=True, zone_factor=False),
        )
        mgr = AdaptiveDecayManager(config)
        item = _make_item(importance=0.5, zone=3)
        days = mgr.effective_decay_days(item)
        # 30 * (0.5 + 0.5) = 30
        assert days == pytest.approx(30.0)

    def test_zone_factor_with_high_zone(self):
        config = DecayConfig(
            decay_days=30, adaptive=AdaptiveDecayConfig(enabled=True)
        )
        mgr = AdaptiveDecayManager(config)
        item = _make_item(importance=0.5, zone=4)
        days = mgr.effective_decay_days(item)
        # zone_multiplier = max(0.5, 2.0 - 4*0.5) = max(0.5, 0.0) = 0.5
        # 30 * 1.0 * 0.5 = 15
        assert days == pytest.approx(15.0)


class TestEffectiveForgetDays:
    def test_basic(self):
        config = DecayConfig(
            auto_forget_days=90, adaptive=AdaptiveDecayConfig(enabled=True)
        )
        mgr = AdaptiveDecayManager(config)
        item = _make_item(importance=0.5)
        days = mgr.effective_forget_days(item)
        # 90 * (0.5 + 0.5) = 90
        assert days == pytest.approx(90.0)

    def test_high_importance_extends_forget(self):
        config = DecayConfig(
            auto_forget_days=90, adaptive=AdaptiveDecayConfig(enabled=True)
        )
        mgr = AdaptiveDecayManager(config)
        item = _make_item(importance=1.0)
        days = mgr.effective_forget_days(item)
        # 90 * (0.5 + 1.0) = 135
        assert days == pytest.approx(135.0)


class TestApplyCurve:
    def test_linear_no_decay(self):
        config = DecayConfig(adaptive=AdaptiveDecayConfig(enabled=True, decay_curve="linear"))
        mgr = AdaptiveDecayManager(config)
        assert mgr.apply_curve(10, 30) == 0.0  # Not yet past threshold

    def test_linear_full_decay(self):
        config = DecayConfig(adaptive=AdaptiveDecayConfig(enabled=True, decay_curve="linear"))
        mgr = AdaptiveDecayManager(config)
        result = mgr.apply_curve(60, 30)
        assert result == pytest.approx(1.0)

    def test_exponential_curve(self):
        config = DecayConfig(
            adaptive=AdaptiveDecayConfig(enabled=True, decay_curve="exponential")
        )
        mgr = AdaptiveDecayManager(config)
        assert mgr.apply_curve(10, 30) == 0.0
        result = mgr.apply_curve(40, 30)
        assert 0.0 < result < 1.0

    def test_sigmoid_curve(self):
        config = DecayConfig(
            adaptive=AdaptiveDecayConfig(enabled=True, decay_curve="sigmoid")
        )
        mgr = AdaptiveDecayManager(config)
        assert mgr.apply_curve(10, 30) == 0.0
        result = mgr.apply_curve(31, 30)
        assert 0.0 < result < 1.0
        # Far past threshold should approach 1
        result_far = mgr.apply_curve(90, 30)
        assert result_far > 0.9


class TestDecayManagerIntegration:
    def test_adaptive_enabled(self):
        config = DecayConfig(
            enabled=True, decay_days=30, auto_forget_days=90,
            min_zone_for_decay=2,
            adaptive=AdaptiveDecayConfig(enabled=True),
        )
        mgr = DecayManager(config)
        assert mgr._adaptive is not None

    def test_adaptive_disabled(self):
        config = DecayConfig(
            enabled=True, adaptive=AdaptiveDecayConfig(enabled=False)
        )
        mgr = DecayManager(config)
        assert mgr._adaptive is None

    def test_adaptive_decay_uses_effective_days(self):
        """High importance items should resist decay longer."""
        now = time.time()
        config = DecayConfig(
            enabled=True, decay_days=30, auto_forget_days=90,
            min_zone_for_decay=2,
            adaptive=AdaptiveDecayConfig(enabled=True, zone_factor=False),
        )
        mgr = DecayManager(config)

        # High importance item recalled 35 days ago
        high_imp = MemoryItem(
            id="high", content="important", zone=2,
            created_at=now - 200 * SECONDS_PER_DAY,
            last_recalled_at=now - 35 * SECONDS_PER_DAY,
            arbitrary_importance=0.9,
        )
        # effective_decay_days = 30 * (0.5+0.9) = 42 → 35 < 42 → no decay
        result = mgr.check_decay([high_imp], now)
        assert len(result.to_demote) == 0

        # Low importance item recalled 35 days ago
        low_imp = MemoryItem(
            id="low", content="trivial", zone=2,
            created_at=now - 200 * SECONDS_PER_DAY,
            last_recalled_at=now - 35 * SECONDS_PER_DAY,
            arbitrary_importance=0.1,
        )
        # effective_decay_days = 30 * (0.5+0.1) = 18 → 35 > 18 → demote
        result = mgr.check_decay([low_imp], now)
        assert len(result.to_demote) == 1
