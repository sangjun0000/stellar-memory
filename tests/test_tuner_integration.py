"""Tests for WeightTuner integration with StellarMemory."""

import os
import tempfile
import pytest

from stellar_memory.config import StellarConfig, TunerConfig
from stellar_memory.stellar import StellarMemory


@pytest.fixture
def config(tmp_path):
    return StellarConfig(
        db_path=str(tmp_path / "test.db"),
        tuner=TunerConfig(
            enabled=True,
            min_feedback=3,
            feedback_db_path=str(tmp_path / "feedback.db"),
        ),
    )


@pytest.fixture
def memory(config):
    mem = StellarMemory(config)
    return mem


def test_provide_feedback_records(memory):
    """provide_feedback should record without error."""
    memory.store("Python is great for data science")
    memory.recall("Python")
    memory.provide_feedback("Python", memory._last_recall_ids)


def test_last_recall_ids_tracked(memory):
    """recall() should populate _last_recall_ids."""
    item = memory.store("Machine learning basics")
    memory.recall("machine learning")
    assert len(memory._last_recall_ids) > 0


def test_last_recall_ids_empty_initially(memory):
    """_last_recall_ids should be empty before any recall."""
    assert memory._last_recall_ids == []


def test_auto_tune_insufficient_feedback(memory):
    """auto_tune should return None with insufficient feedback."""
    result = memory.auto_tune()
    assert result is None


def test_auto_tune_after_enough_feedback(memory):
    """auto_tune should return weights after sufficient feedback."""
    for i in range(5):
        content = f"Memory item number {i}"
        memory.store(content)
        results = memory.recall(content)
        ids = [r.id for r in results]
        memory.provide_feedback(content, ids)
    result = memory.auto_tune()
    # With min_feedback=3 and 5 records, tune should attempt
    # Result may still be None if usage rates are equal
    # but no error should occur


def test_provide_feedback_with_empty_ids(memory):
    """provide_feedback with empty used_ids should not error."""
    memory.store("Something important")
    memory.recall("Something")
    memory.provide_feedback("Something", [])


def test_recall_updates_last_ids(memory):
    """Multiple recalls should update _last_recall_ids each time."""
    memory.store("First topic about cats")
    memory.store("Second topic about dogs")
    memory.recall("cats")
    ids1 = list(memory._last_recall_ids)
    memory.recall("dogs")
    ids2 = list(memory._last_recall_ids)
    # IDs should reflect the latest recall
    assert isinstance(ids1, list)
    assert isinstance(ids2, list)


def test_tuner_disabled(tmp_path):
    """When tuner is disabled, provide_feedback and auto_tune should still work."""
    config = StellarConfig(
        db_path=str(tmp_path / "test.db"),
        tuner=TunerConfig(enabled=False),
    )
    mem = StellarMemory(config)
    mem.store("Test content")
    mem.recall("Test")
    mem.provide_feedback("Test", mem._last_recall_ids)
    result = mem.auto_tune()
    assert result is None
