"""Weight auto-tuner - adjusts memory function weights based on user feedback."""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.config import TunerConfig, MemoryFunctionConfig

from stellar_memory.models import FeedbackRecord

logger = logging.getLogger(__name__)


class WeightTuner:
    """Adjusts w_recall, w_freshness, w_arbitrary, w_context based on feedback."""

    def __init__(self, tuner_config: TunerConfig | None = None,
                 memory_config: MemoryFunctionConfig | None = None):
        from stellar_memory.config import TunerConfig as _TC, MemoryFunctionConfig as _MC
        self._tcfg = tuner_config or _TC()
        self._mcfg = memory_config or _MC()
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _init_db(self) -> None:
        self._conn = sqlite3.connect(self._tcfg.feedback_db_path)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                result_ids TEXT,
                used_ids TEXT,
                timestamp REAL NOT NULL,
                weights_snapshot TEXT
            )
        """)
        self._conn.commit()

    def record_feedback(self, record: FeedbackRecord) -> None:
        if self._conn is None:
            return
        record.timestamp = record.timestamp or time.time()
        record.weights_snapshot = {
            "w_recall": self._mcfg.w_recall,
            "w_freshness": self._mcfg.w_freshness,
            "w_arbitrary": self._mcfg.w_arbitrary,
            "w_context": self._mcfg.w_context,
        }
        self._conn.execute(
            "INSERT INTO feedback (query, result_ids, used_ids, timestamp, weights_snapshot) "
            "VALUES (?, ?, ?, ?, ?)",
            (record.query, json.dumps(record.result_ids), json.dumps(record.used_ids),
             record.timestamp, json.dumps(record.weights_snapshot)),
        )
        self._conn.commit()

    def get_feedback_count(self) -> int:
        if self._conn is None:
            return 0
        cur = self._conn.execute("SELECT COUNT(*) FROM feedback")
        return cur.fetchone()[0]

    def tune(self) -> dict[str, float] | None:
        """Analyze feedback and adjust weights. Returns new weights or None if insufficient data."""
        count = self.get_feedback_count()
        if count < self._tcfg.min_feedback:
            logger.info("Not enough feedback (%d/%d) for tuning", count, self._tcfg.min_feedback)
            return None

        cur = self._conn.execute(
            "SELECT result_ids, used_ids FROM feedback ORDER BY timestamp DESC LIMIT ?",
            (self._tcfg.min_feedback,),
        )
        rows = cur.fetchall()

        total_results = 0
        total_used = 0
        for result_ids_json, used_ids_json in rows:
            result_ids = json.loads(result_ids_json)
            used_ids = json.loads(used_ids_json)
            total_results += len(result_ids)
            total_used += len(used_ids)

        if total_results == 0:
            return None

        usage_rate = total_used / total_results

        weights = {
            "w_recall": self._mcfg.w_recall,
            "w_freshness": self._mcfg.w_freshness,
            "w_arbitrary": self._mcfg.w_arbitrary,
            "w_context": self._mcfg.w_context,
        }

        if usage_rate < 0.3:
            weights["w_context"] += self._tcfg.max_delta
            weights["w_freshness"] -= self._tcfg.max_delta / 2
            weights["w_recall"] -= self._tcfg.max_delta / 2
        elif usage_rate > 0.7:
            weights["w_recall"] += self._tcfg.max_delta / 2
            weights["w_freshness"] += self._tcfg.max_delta / 2
            weights["w_context"] -= self._tcfg.max_delta
        else:
            logger.info("Usage rate %.2f is acceptable, no tuning needed", usage_rate)
            return None

        weights = self._clamp_and_normalize(weights)
        self._apply_weights(weights)
        logger.info("Weights tuned: %s (usage_rate=%.2f)", weights, usage_rate)
        return weights

    def _clamp_and_normalize(self, weights: dict[str, float]) -> dict[str, float]:
        for key in weights:
            weights[key] = max(self._tcfg.weight_min, min(self._tcfg.weight_max, weights[key]))
        total = sum(weights.values())
        if total > 0:
            for key in weights:
                weights[key] = round(weights[key] / total, 4)
        return weights

    def _apply_weights(self, weights: dict[str, float]) -> None:
        self._mcfg.w_recall = weights["w_recall"]
        self._mcfg.w_freshness = weights["w_freshness"]
        self._mcfg.w_arbitrary = weights["w_arbitrary"]
        self._mcfg.w_context = weights["w_context"]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


class NullTuner:
    """No-op tuner when tuning is disabled."""

    def record_feedback(self, record: FeedbackRecord) -> None:
        pass

    def get_feedback_count(self) -> int:
        return 0

    def tune(self) -> None:
        return None

    def close(self) -> None:
        pass


def create_tuner(
    tuner_config: TunerConfig | None = None,
    memory_config: MemoryFunctionConfig | None = None,
) -> WeightTuner | NullTuner:
    from stellar_memory.config import TunerConfig as _TC
    cfg = tuner_config or _TC()
    if not cfg.enabled:
        return NullTuner()
    return WeightTuner(cfg, memory_config)
