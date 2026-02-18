"""P9-F2: Self-Learning - automatic weight optimization from recall patterns."""

from __future__ import annotations

import json
import logging
import sqlite3
import time

from stellar_memory.config import MemoryFunctionConfig, SelfLearningConfig
from stellar_memory.models import RecallLog, OptimizationReport

logger = logging.getLogger(__name__)

WEIGHT_KEYS = ["w_recall", "w_freshness", "w_arbitrary", "w_context", "w_emotion"]


class PatternCollector:
    """Collects and analyzes recall patterns."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self._db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recall_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                result_ids TEXT NOT NULL,
                timestamp REAL NOT NULL,
                feedback TEXT DEFAULT 'none'
            )
        """)
        conn.commit()
        conn.close()

    def log_recall(self, query: str, result_ids: list[str]):
        """Record a recall event."""
        conn = sqlite3.connect(self._db_path)
        conn.execute(
            "INSERT INTO recall_logs (query, result_ids, timestamp, feedback) VALUES (?, ?, ?, ?)",
            (query, json.dumps(result_ids), time.time(), "none"),
        )
        conn.commit()
        conn.close()

    def log_feedback(self, query: str, feedback: str):
        """Update feedback for the most recent matching recall."""
        conn = sqlite3.connect(self._db_path)
        conn.execute(
            "UPDATE recall_logs SET feedback = ? WHERE id = ("
            "  SELECT id FROM recall_logs WHERE query = ? ORDER BY timestamp DESC LIMIT 1"
            ")",
            (feedback, query),
        )
        conn.commit()
        conn.close()

    def get_logs(self, limit: int = 1000) -> list[RecallLog]:
        """Get recent recall logs."""
        conn = sqlite3.connect(self._db_path)
        rows = conn.execute(
            "SELECT query, result_ids, timestamp, feedback FROM recall_logs "
            "ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return [
            RecallLog(
                query=row[0],
                result_ids=json.loads(row[1]),
                timestamp=row[2],
                feedback=row[3],
            )
            for row in rows
        ]

    def get_log_count(self) -> int:
        """Get total number of recall logs."""
        conn = sqlite3.connect(self._db_path)
        count = conn.execute("SELECT COUNT(*) FROM recall_logs").fetchone()[0]
        conn.close()
        return count

    def analyze_patterns(self, logs: list[RecallLog]) -> dict:
        """Analyze recall patterns.

        Returns:
            dict with preference scores for each weight dimension.
        """
        if not logs:
            return {
                "freshness_preference": 0.0,
                "emotion_preference": 0.0,
                "recall_frequency": 0.0,
                "topic_diversity": 0.0,
            }

        # Freshness preference: how many recalls target recent items
        positive_count = sum(1 for log in logs if log.feedback == "positive")
        negative_count = sum(1 for log in logs if log.feedback == "negative")
        total_feedback = positive_count + negative_count

        # Recall frequency: average results per query
        avg_results = sum(len(log.result_ids) for log in logs) / len(logs)
        recall_frequency = min(avg_results / 10.0, 1.0)

        # Topic diversity: unique queries / total queries
        unique_queries = len(set(log.query.lower().strip() for log in logs))
        topic_diversity = min(unique_queries / len(logs), 1.0)

        # Freshness preference from positive feedback ratio
        freshness_preference = 0.5
        if total_feedback > 0:
            freshness_preference = positive_count / total_feedback

        # Emotion preference: presence of emotion-related keywords
        emotion_keywords = {"happy", "sad", "angry", "afraid", "surprised", "love", "hate",
                           "frustrated", "excited", "anxious", "relieved", "joy"}
        emotion_queries = sum(
            1 for log in logs
            if any(kw in log.query.lower() for kw in emotion_keywords)
        )
        emotion_preference = min(emotion_queries / max(len(logs), 1), 1.0)

        return {
            "freshness_preference": round(freshness_preference, 3),
            "emotion_preference": round(emotion_preference, 3),
            "recall_frequency": round(recall_frequency, 3),
            "topic_diversity": round(topic_diversity, 3),
        }


class WeightOptimizer:
    """Memory function weight optimizer."""

    def __init__(self, config: MemoryFunctionConfig, sl_config: SelfLearningConfig,
                 db_path: str):
        self._config = config
        self._sl_config = sl_config
        self._db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self._db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weight_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                weights TEXT NOT NULL,
                timestamp REAL NOT NULL,
                reason TEXT DEFAULT ''
            )
        """)
        conn.commit()
        conn.close()

    def optimize(self, patterns: dict, logs: list[RecallLog]) -> OptimizationReport:
        """Optimize weights based on patterns.

        Raises:
            ValueError: If not enough logs for optimization.
        """
        if len(logs) < self._sl_config.min_logs:
            raise ValueError(
                f"Need at least {self._sl_config.min_logs} recall logs, "
                f"got {len(logs)}"
            )

        # Save current weights
        before = self._get_current_weights()
        self._save_weights(before, reason="pre_optimize")

        # Calculate new weights
        lr = self._sl_config.learning_rate
        max_delta = self._sl_config.max_delta
        new_weights = dict(before)

        # Adjust based on patterns
        if patterns.get("freshness_preference", 0.5) > 0.6:
            delta = min(lr, max_delta)
            new_weights["w_freshness"] += delta
        elif patterns.get("freshness_preference", 0.5) < 0.4:
            delta = min(lr, max_delta)
            new_weights["w_freshness"] -= delta

        if patterns.get("emotion_preference", 0.0) > 0.3:
            delta = min(lr, max_delta)
            new_weights["w_emotion"] += delta

        if patterns.get("recall_frequency", 0.0) > 0.6:
            delta = min(lr, max_delta)
            new_weights["w_recall"] += delta

        if patterns.get("topic_diversity", 0.0) > 0.7:
            delta = min(lr, max_delta)
            new_weights["w_context"] += delta

        # Clamp and normalize
        new_weights = self._clamp_weights(new_weights)
        new_weights = self._normalize_weights(new_weights)

        # Simulate
        old_score = self._simulate(before, logs)
        new_score = self._simulate(new_weights, logs)

        pattern_desc = self._describe_pattern(patterns)

        if new_score >= old_score:
            # Apply new weights
            self._apply_weights(new_weights)
            self._save_weights(new_weights, reason="optimize")
            return OptimizationReport(
                before_weights=before,
                after_weights=new_weights,
                improvement=f"Score improved: {old_score:.3f} -> {new_score:.3f}",
                pattern=pattern_desc,
                simulation_score=new_score,
                rolled_back=False,
            )
        else:
            # No improvement, don't apply
            return OptimizationReport(
                before_weights=before,
                after_weights=before,
                improvement=f"No improvement: {old_score:.3f} vs {new_score:.3f}",
                pattern=pattern_desc,
                simulation_score=old_score,
                rolled_back=True,
            )

    def rollback(self) -> dict[str, float]:
        """Rollback to previous weights from history."""
        conn = sqlite3.connect(self._db_path)
        rows = conn.execute(
            "SELECT weights FROM weight_history ORDER BY timestamp DESC LIMIT 2"
        ).fetchall()
        conn.close()

        if len(rows) < 2:
            return self._get_current_weights()

        # rows[0] is current, rows[1] is previous
        prev_weights = json.loads(rows[1][0])
        self._apply_weights(prev_weights)
        self._save_weights(prev_weights, reason="rollback")
        return prev_weights

    def get_weight_history(self, limit: int = 10) -> list[dict]:
        """Get weight change history."""
        conn = sqlite3.connect(self._db_path)
        rows = conn.execute(
            "SELECT weights, timestamp, reason FROM weight_history "
            "ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return [
            {"weights": json.loads(row[0]), "timestamp": row[1], "reason": row[2]}
            for row in rows
        ]

    def _get_current_weights(self) -> dict[str, float]:
        return {
            "w_recall": self._config.w_recall,
            "w_freshness": self._config.w_freshness,
            "w_arbitrary": self._config.w_arbitrary,
            "w_context": self._config.w_context,
            "w_emotion": self._config.w_emotion,
        }

    def _save_weights(self, weights: dict, reason: str = ""):
        conn = sqlite3.connect(self._db_path)
        conn.execute(
            "INSERT INTO weight_history (weights, timestamp, reason) VALUES (?, ?, ?)",
            (json.dumps(weights), time.time(), reason),
        )
        conn.commit()
        conn.close()

    def _apply_weights(self, weights: dict):
        """Apply weights to the config object."""
        for key in WEIGHT_KEYS:
            if key in weights:
                setattr(self._config, key, weights[key])

    def _clamp_weights(self, weights: dict) -> dict:
        """Clamp weights to valid range."""
        return {
            k: max(0.01, min(0.8, v))
            for k, v in weights.items()
        }

    def _normalize_weights(self, weights: dict) -> dict:
        """Normalize weights to sum to 1.0."""
        total = sum(weights.values())
        if total == 0:
            n = len(weights)
            return {k: round(1.0 / n, 4) for k in weights}
        return {k: round(v / total, 4) for k, v in weights.items()}

    def _simulate(self, weights: dict, logs: list[RecallLog]) -> float:
        """Simulate scoring with given weights.

        Returns average "match score" based on how many results each query returned.
        Higher is better (more results = weights favoring useful content).
        """
        if not logs:
            return 0.0

        scores = []
        for log in logs[-100:]:  # Use last 100 logs
            # Simple heuristic: more results with positive feedback = better
            result_count = len(log.result_ids)
            base_score = min(result_count / 5.0, 1.0)

            if log.feedback == "positive":
                base_score *= 1.2
            elif log.feedback == "negative":
                base_score *= 0.5

            # Weight influence on score (higher diversity weight = broader results)
            w_diversity = weights.get("w_context", 0.15) + weights.get("w_arbitrary", 0.25)
            score = base_score * (0.5 + w_diversity)
            scores.append(min(score, 1.0))

        return sum(scores) / len(scores)

    def _describe_pattern(self, patterns: dict) -> str:
        """Describe detected pattern."""
        parts = []
        if patterns.get("freshness_preference", 0.5) > 0.6:
            parts.append("freshness_preferred")
        if patterns.get("emotion_preference", 0.0) > 0.3:
            parts.append("emotion_sensitive")
        if patterns.get("recall_frequency", 0.0) > 0.6:
            parts.append("high_recall_frequency")
        if patterns.get("topic_diversity", 0.0) > 0.7:
            parts.append("diverse_topics")
        return ", ".join(parts) if parts else "balanced"
