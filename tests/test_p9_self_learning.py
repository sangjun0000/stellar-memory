"""Tests for P9-F2: Self-Learning."""

import os
import tempfile
import pytest

from stellar_memory.config import MemoryFunctionConfig, SelfLearningConfig
from stellar_memory.self_learning import PatternCollector, WeightOptimizer
from stellar_memory.models import RecallLog, OptimizationReport


@pytest.fixture
def tmp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


class TestPatternCollector:
    def test_log_and_get(self, tmp_db):
        pc = PatternCollector(tmp_db)
        pc.log_recall("test query", ["id1", "id2"])
        logs = pc.get_logs(limit=10)
        assert len(logs) == 1
        assert logs[0].query == "test query"
        assert logs[0].result_ids == ["id1", "id2"]

    def test_multiple_logs(self, tmp_db):
        pc = PatternCollector(tmp_db)
        for i in range(5):
            pc.log_recall(f"query_{i}", [f"id_{i}"])
        logs = pc.get_logs(limit=10)
        assert len(logs) == 5

    def test_get_logs_limit(self, tmp_db):
        pc = PatternCollector(tmp_db)
        for i in range(10):
            pc.log_recall(f"query_{i}", [f"id_{i}"])
        logs = pc.get_logs(limit=3)
        assert len(logs) == 3

    def test_get_log_count(self, tmp_db):
        pc = PatternCollector(tmp_db)
        assert pc.get_log_count() == 0
        pc.log_recall("q1", ["id1"])
        pc.log_recall("q2", ["id2"])
        assert pc.get_log_count() == 2

    def test_log_feedback(self, tmp_db):
        pc = PatternCollector(tmp_db)
        pc.log_recall("test", ["id1"])
        pc.log_feedback("test", "positive")
        logs = pc.get_logs()
        assert logs[0].feedback == "positive"

    def test_analyze_patterns_empty(self, tmp_db):
        pc = PatternCollector(tmp_db)
        patterns = pc.analyze_patterns([])
        assert patterns["freshness_preference"] == 0.0
        assert patterns["recall_frequency"] == 0.0

    def test_analyze_patterns_with_data(self, tmp_db):
        pc = PatternCollector(tmp_db)
        logs = [
            RecallLog(query="python basics", result_ids=["a", "b", "c"],
                      timestamp=1000.0, feedback="positive"),
            RecallLog(query="happy memories", result_ids=["d"],
                      timestamp=1001.0, feedback="none"),
        ]
        patterns = pc.analyze_patterns(logs)
        assert 0.0 <= patterns["freshness_preference"] <= 1.0
        assert 0.0 <= patterns["emotion_preference"] <= 1.0
        assert 0.0 <= patterns["recall_frequency"] <= 1.0
        assert 0.0 <= patterns["topic_diversity"] <= 1.0

    def test_analyze_emotion_keywords(self, tmp_db):
        pc = PatternCollector(tmp_db)
        logs = [
            RecallLog(query="happy moment", result_ids=["a"], timestamp=1000.0),
            RecallLog(query="angry feeling", result_ids=["b"], timestamp=1001.0),
            RecallLog(query="excited about", result_ids=["c"], timestamp=1002.0),
        ]
        patterns = pc.analyze_patterns(logs)
        assert patterns["emotion_preference"] > 0.0

    def test_analyze_topic_diversity(self, tmp_db):
        pc = PatternCollector(tmp_db)
        # All unique queries → high diversity
        logs = [
            RecallLog(query=f"unique_topic_{i}", result_ids=["a"], timestamp=float(i))
            for i in range(10)
        ]
        patterns = pc.analyze_patterns(logs)
        assert patterns["topic_diversity"] == 1.0


class TestWeightOptimizer:
    def setup_method(self):
        self.mf_config = MemoryFunctionConfig(
            w_recall=0.3, w_freshness=0.3, w_arbitrary=0.25,
            w_context=0.15, w_emotion=0.0,
        )
        self.sl_config = SelfLearningConfig(
            enabled=True, learning_rate=0.03, min_logs=5, max_delta=0.1,
        )

    def test_optimize_insufficient_logs(self, tmp_db):
        opt = WeightOptimizer(self.mf_config, self.sl_config, tmp_db)
        logs = [RecallLog(query="q", result_ids=["a"], timestamp=1.0)]
        patterns = {"freshness_preference": 0.5}
        with pytest.raises(ValueError, match="Need at least"):
            opt.optimize(patterns, logs)

    def test_optimize_success(self, tmp_db):
        opt = WeightOptimizer(self.mf_config, self.sl_config, tmp_db)
        logs = [
            RecallLog(query=f"q_{i}", result_ids=["a", "b"], timestamp=float(i), feedback="positive")
            for i in range(10)
        ]
        patterns = {
            "freshness_preference": 0.8,
            "emotion_preference": 0.0,
            "recall_frequency": 0.3,
            "topic_diversity": 0.5,
        }
        report = opt.optimize(patterns, logs)
        assert isinstance(report, OptimizationReport)
        assert report.before_weights is not None
        assert report.after_weights is not None

    def test_weights_normalized_after_optimize(self, tmp_db):
        opt = WeightOptimizer(self.mf_config, self.sl_config, tmp_db)
        logs = [
            RecallLog(query=f"q_{i}", result_ids=["a"], timestamp=float(i))
            for i in range(10)
        ]
        patterns = {"freshness_preference": 0.8}
        report = opt.optimize(patterns, logs)
        total = sum(report.after_weights.values())
        assert abs(total - 1.0) < 0.01

    def test_rollback(self, tmp_db):
        opt = WeightOptimizer(self.mf_config, self.sl_config, tmp_db)
        logs = [
            RecallLog(query=f"q_{i}", result_ids=["a", "b"], timestamp=float(i))
            for i in range(10)
        ]
        patterns = {"freshness_preference": 0.8}
        opt.optimize(patterns, logs)
        prev = opt.rollback()
        assert isinstance(prev, dict)
        assert "w_recall" in prev

    def test_get_weight_history(self, tmp_db):
        opt = WeightOptimizer(self.mf_config, self.sl_config, tmp_db)
        logs = [
            RecallLog(query=f"q_{i}", result_ids=["a"], timestamp=float(i))
            for i in range(10)
        ]
        patterns = {"freshness_preference": 0.8}
        opt.optimize(patterns, logs)
        history = opt.get_weight_history(limit=5)
        assert len(history) >= 1
        assert "weights" in history[0]
        assert "reason" in history[0]

    def test_weight_clamping(self, tmp_db):
        opt = WeightOptimizer(self.mf_config, self.sl_config, tmp_db)
        clamped = opt._clamp_weights({"w_recall": -0.5, "w_freshness": 1.5})
        assert clamped["w_recall"] == 0.01
        assert clamped["w_freshness"] == 0.8

    def test_normalize_weights(self, tmp_db):
        opt = WeightOptimizer(self.mf_config, self.sl_config, tmp_db)
        normalized = opt._normalize_weights({"a": 2.0, "b": 3.0})
        total = sum(normalized.values())
        assert abs(total - 1.0) < 0.01

    def test_normalize_zero_weights(self, tmp_db):
        opt = WeightOptimizer(self.mf_config, self.sl_config, tmp_db)
        normalized = opt._normalize_weights({"a": 0.0, "b": 0.0})
        assert all(v > 0 for v in normalized.values())
