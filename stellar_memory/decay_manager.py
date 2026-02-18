"""Memory decay manager - automatic forgetting of stale memories."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.config import EmotionConfig

from stellar_memory.config import DecayConfig
from stellar_memory.models import MemoryItem, DecayResult

logger = logging.getLogger(__name__)

SECONDS_PER_DAY = 86400


class DecayManager:
    """Manages automatic memory decay and forgetting."""

    def __init__(self, config: DecayConfig,
                 emotion_config: EmotionConfig | None = None):
        self._config = config
        self._emotion_config = emotion_config
        self._adaptive = None
        if config.adaptive.enabled:
            from stellar_memory.adaptive_decay import AdaptiveDecayManager
            self._adaptive = AdaptiveDecayManager(config)

    def _adjusted_decay_days(self, item: MemoryItem, base_days: int) -> int:
        """Adjust decay days based on emotion intensity."""
        if self._emotion_config is None or item.emotion is None:
            return base_days
        intensity = item.emotion.intensity
        if intensity >= self._emotion_config.decay_boost_threshold:
            return int(base_days / self._emotion_config.decay_boost_factor)
        if intensity <= self._emotion_config.decay_penalty_threshold:
            return int(base_days * self._emotion_config.decay_penalty_factor)
        return base_days

    def check_decay(self, items: list[MemoryItem],
                    current_time: float) -> DecayResult:
        """Check which items should decay or be forgotten."""
        result = DecayResult()
        if not self._config.enabled:
            return result

        for item in items:
            if item.zone < self._config.min_zone_for_decay:
                continue

            if self._adaptive:
                decay_days = self._adaptive.effective_decay_days(item)
                forget_days = self._adaptive.effective_forget_days(item)
            else:
                decay_days = self._config.decay_days
                forget_days = self._config.auto_forget_days

            # P7: Adjust decay based on emotion intensity
            decay_days = self._adjusted_decay_days(item, decay_days)
            forget_days = self._adjusted_decay_days(item, forget_days)

            decay_threshold = current_time - (decay_days * SECONDS_PER_DAY)
            forget_threshold = current_time - (forget_days * SECONDS_PER_DAY)

            if (item.zone == 4
                    and item.last_recalled_at < forget_threshold):
                result.to_forget.append(item.id)
            elif item.last_recalled_at < decay_threshold:
                result.to_demote.append((item.id, item.zone, item.zone + 1))

        return result
