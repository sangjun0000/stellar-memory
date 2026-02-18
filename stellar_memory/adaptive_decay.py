"""Adaptive decay - importance-based differential forgetting rates."""

from __future__ import annotations

import math

from stellar_memory.config import DecayConfig
from stellar_memory.models import MemoryItem

SECONDS_PER_DAY = 86400


class AdaptiveDecayManager:
    """Manages importance-based differential decay rates."""

    def __init__(self, decay_config: DecayConfig):
        self._config = decay_config
        self._adaptive = decay_config.adaptive

    def effective_decay_days(self, item: MemoryItem) -> float:
        """Calculate effective decay days based on importance.

        Formula: base_days * (0.5 + importance * weight)
        - importance=0.9, weight=1.0 → 30 * 1.4 = 42 days
        - importance=0.3, weight=1.0 → 30 * 0.8 = 24 days
        - importance=0.0, weight=1.0 → 30 * 0.5 = 15 days
        """
        base = self._config.decay_days
        importance = item.arbitrary_importance
        weight = self._adaptive.importance_weight
        factor = 0.5 + importance * weight

        if self._adaptive.zone_factor and item.zone > 0:
            zone_multiplier = max(0.5, 2.0 - item.zone * 0.5)
            factor *= zone_multiplier

        return base * factor

    def effective_forget_days(self, item: MemoryItem) -> float:
        """Calculate effective auto-forget days."""
        base = self._config.auto_forget_days
        importance = item.arbitrary_importance
        return base * (0.5 + importance * self._adaptive.importance_weight)

    def apply_curve(self, elapsed_days: float, threshold_days: float) -> float:
        """Apply decay curve. Returns 0.0 (no decay) to 1.0 (full decay)."""
        if elapsed_days < threshold_days:
            return 0.0
        ratio = elapsed_days / threshold_days

        if self._adaptive.decay_curve == "exponential":
            return min(1.0, 1.0 - math.exp(-(ratio - 1.0)))
        elif self._adaptive.decay_curve == "sigmoid":
            x = (ratio - 1.0) * 5
            return 1.0 / (1.0 + math.exp(-x))
        else:  # linear
            return min(1.0, ratio - 1.0)
