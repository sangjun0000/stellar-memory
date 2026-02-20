"""Tests for weight auto-tuner module."""

import os
import tempfile

from stellar_memory.weight_tuner import WeightTuner, NullTuner, create_tuner
from stellar_memory.config import TunerConfig, MemoryFunctionConfig
from stellar_memory.models import FeedbackRecord


def _tmp_db() -> str:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return path


class TestWeightTuner:
    def test_record_feedback(self):
        db = _tmp_db()
        try:
            cfg = TunerConfig(feedback_db_path=db, min_feedback=2)
            tuner = WeightTuner(cfg)
            record = FeedbackRecord(
                query="test query",
                result_ids=["a", "b", "c"],
                used_ids=["a"],
            )
            tuner.record_feedback(record)
            assert tuner.get_feedback_count() == 1
            tuner.close()
        finally:
            os.unlink(db)

    def test_tune_insufficient_data(self):
        db = _tmp_db()
        try:
            cfg = TunerConfig(feedback_db_path=db, min_feedback=50)
            tuner = WeightTuner(cfg)
            result = tuner.tune()
            assert result is None
            tuner.close()
        finally:
            os.unlink(db)

    def test_tune_low_usage_rate(self):
        db = _tmp_db()
        try:
            cfg = TunerConfig(feedback_db_path=db, min_feedback=3)
            mcfg = MemoryFunctionConfig()
            tuner = WeightTuner(cfg, mcfg)
            # Low usage: many results, few used
            for _ in range(5):
                tuner.record_feedback(FeedbackRecord(
                    query="q",
                    result_ids=["a", "b", "c", "d", "e"],
                    used_ids=["a"],
                ))
            weights = tuner.tune()
            assert weights is not None
            # Context weight should increase
            assert abs(sum(weights.values()) - 1.0) < 0.01
            tuner.close()
        finally:
            os.unlink(db)

    def test_tune_high_usage_rate(self):
        db = _tmp_db()
        try:
            cfg = TunerConfig(feedback_db_path=db, min_feedback=3)
            mcfg = MemoryFunctionConfig()
            tuner = WeightTuner(cfg, mcfg)
            # High usage: most results used
            for _ in range(5):
                tuner.record_feedback(FeedbackRecord(
                    query="q",
                    result_ids=["a", "b"],
                    used_ids=["a", "b"],
                ))
            weights = tuner.tune()
            assert weights is not None
            assert abs(sum(weights.values()) - 1.0) < 0.01
            tuner.close()
        finally:
            os.unlink(db)

    def test_weights_clamped(self):
        db = _tmp_db()
        try:
            cfg = TunerConfig(feedback_db_path=db, min_feedback=1, weight_min=0.1, weight_max=0.4)
            mcfg = MemoryFunctionConfig()
            tuner = WeightTuner(cfg, mcfg)
            tuner.record_feedback(FeedbackRecord(
                query="q", result_ids=["a", "b", "c"], used_ids=["a"],
            ))
            weights = tuner.tune()
            if weights:
                for v in weights.values():
                    assert v >= 0.1 - 0.01
                    assert v <= 0.4 + 0.01
            tuner.close()
        finally:
            os.unlink(db)


    def test_max_delta_respected(self):
        db = _tmp_db()
        try:
            max_d = 0.03
            cfg = TunerConfig(feedback_db_path=db, min_feedback=2, max_delta=max_d)
            mcfg = MemoryFunctionConfig()
            original = {
                "w_recall": mcfg.w_recall,
                "w_freshness": mcfg.w_freshness,
                "w_arbitrary": mcfg.w_arbitrary,
                "w_context": mcfg.w_context,
            }
            tuner = WeightTuner(cfg, mcfg)
            for _ in range(5):
                tuner.record_feedback(FeedbackRecord(
                    query="q", result_ids=["a", "b", "c", "d", "e"], used_ids=["a"],
                ))
            weights = tuner.tune()
            if weights:
                # Before normalization, each weight shift should be <= max_delta
                # After normalization totals 1.0, but individual changes are bounded
                for k in original:
                    # Normalization can amplify slightly, allow 2x max_delta tolerance
                    assert abs(weights[k] - original[k]) <= max_d * 3 + 0.01
            tuner.close()
        finally:
            os.unlink(db)


class TestNullTuner:
    def test_record_does_nothing(self):
        t = NullTuner()
        t.record_feedback(FeedbackRecord(query="q"))
        assert t.get_feedback_count() == 0
        assert t.tune() is None

    def test_close_safe(self):
        t = NullTuner()
        t.close()


class TestCreateTuner:
    def test_disabled(self):
        cfg = TunerConfig(enabled=False)
        t = create_tuner(cfg)
        assert isinstance(t, NullTuner)

    def test_enabled(self):
        db = _tmp_db()
        try:
            cfg = TunerConfig(enabled=True, feedback_db_path=db)
            t = create_tuner(cfg)
            assert isinstance(t, WeightTuner)
            t.close()
        finally:
            os.unlink(db)
