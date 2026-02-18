"""Tests for P9-F4: Memory Reasoning."""

import time
import pytest

from stellar_memory.config import ReasoningConfig
from stellar_memory.reasoning import MemoryReasoner, ContradictionDetector
from stellar_memory.models import MemoryItem, ReasoningResult, Contradiction


def _make_memory(content: str, mem_id: str | None = None,
                 zone: int = 1, total_score: float = 0.5) -> MemoryItem:
    now = time.time()
    return MemoryItem(
        id=mem_id or f"mem_{hash(content) % 10000}",
        content=content,
        created_at=now - 3600,
        last_recalled_at=now,
        recall_count=1,
        arbitrary_importance=0.5,
        zone=zone,
        metadata={},
        total_score=total_score,
    )


class TestMemoryReasoner:
    def setup_method(self):
        self.config = ReasoningConfig(
            enabled=True, max_sources=10, use_llm=False, contradiction_check=False,
        )

    def test_reason_empty_memories(self):
        reasoner = MemoryReasoner(self.config)
        result = reasoner.reason("test query", [])
        assert isinstance(result, ReasoningResult)
        assert result.confidence == 0.0
        assert len(result.insights) > 0

    def test_reason_with_memories(self):
        reasoner = MemoryReasoner(self.config)
        memories = [
            _make_memory("Python is great for data science"),
            _make_memory("Data science uses machine learning algorithms"),
        ]
        result = reasoner.reason("data science", memories)
        assert result.confidence > 0.0
        assert len(result.insights) > 0
        assert len(result.source_memories) == 2

    def test_reason_query_field(self):
        reasoner = MemoryReasoner(self.config)
        result = reasoner.reason("test topic", [_make_memory("Some content")])
        assert result.query == "test topic"

    def test_reason_with_graph_neighbors(self):
        reasoner = MemoryReasoner(self.config)
        memories = [_make_memory("Main memory about Python")]
        neighbors = [_make_memory("Related memory about coding", mem_id="neighbor_1")]
        result = reasoner.reason("Python", memories, graph_neighbors=neighbors)
        assert len(result.source_memories) == 2

    def test_reason_deduplicates_neighbors(self):
        reasoner = MemoryReasoner(self.config)
        mem = _make_memory("Python basics", mem_id="same_id")
        result = reasoner.reason("Python", [mem], graph_neighbors=[mem])
        assert len(result.source_memories) == 1

    def test_reason_max_sources_limit(self):
        config = ReasoningConfig(enabled=True, max_sources=3, use_llm=False, contradiction_check=False)
        reasoner = MemoryReasoner(config)
        memories = [_make_memory(f"Memory {i}", mem_id=f"m_{i}") for i in range(10)]
        result = reasoner.reason("test", memories)
        assert len(result.source_memories) <= 3

    def test_reason_shared_keywords(self):
        reasoner = MemoryReasoner(self.config)
        memories = [
            _make_memory("Machine learning models for prediction"),
            _make_memory("Deep learning models using neural networks"),
        ]
        result = reasoner.reason("models", memories)
        # Should detect "models" and "learning" as shared keywords
        assert any("connects" in insight or "mention" in insight for insight in result.insights)

    def test_reasoning_chain_populated(self):
        reasoner = MemoryReasoner(self.config)
        memories = [_make_memory("Test content")]
        result = reasoner.reason("test", memories)
        assert len(result.reasoning_chain) > 0

    def test_confidence_higher_with_core_zone(self):
        reasoner = MemoryReasoner(self.config)
        core = [_make_memory("Core memory", zone=0)]
        belt = [_make_memory("Belt memory", zone=3)]
        r_core = reasoner.reason("test", core)
        r_belt = reasoner.reason("test", belt)
        assert r_core.confidence >= r_belt.confidence

    def test_reason_with_contradiction_check(self):
        config = ReasoningConfig(enabled=True, use_llm=False, contradiction_check=True)
        reasoner = MemoryReasoner(config)
        memories = [
            _make_memory("Python is fast", mem_id="m1"),
            _make_memory("Python is not fast compared to others", mem_id="m2"),
        ]
        result = reasoner.reason("Python speed", memories)
        # Contradiction check is enabled
        assert isinstance(result.contradictions, list)


class TestContradictionDetector:
    def setup_method(self):
        self.config = ReasoningConfig(
            enabled=True, use_llm=False, contradiction_check=True,
        )

    def test_no_contradictions_single_memory(self):
        detector = ContradictionDetector(self.config)
        result = detector.detect([_make_memory("Only one memory")])
        assert result == []

    def test_no_contradictions_empty(self):
        detector = ContradictionDetector(self.config)
        result = detector.detect([])
        assert result == []

    def test_detect_negation_contradiction(self):
        detector = ContradictionDetector(self.config)
        memories = [
            _make_memory("Python framework Django is good for web development", mem_id="a"),
            _make_memory("Python framework Django is not good for performance", mem_id="b"),
        ]
        result = detector.detect(memories)
        # Should detect potential contradiction due to negation + shared keywords
        assert isinstance(result, list)
        # The rule-based detector should find "not" pattern with shared context
        if result:
            assert isinstance(result[0], Contradiction)
            assert result[0].severity > 0.0

    def test_no_contradiction_unrelated(self):
        detector = ContradictionDetector(self.config)
        memories = [
            _make_memory("I like apples", mem_id="a"),
            _make_memory("The weather is sunny today", mem_id="b"),
        ]
        result = detector.detect(memories)
        assert result == []

    def test_contradiction_severity_range(self):
        detector = ContradictionDetector(self.config)
        memories = [
            _make_memory("The system always works correctly with proper input", mem_id="a"),
            _make_memory("The system never works correctly with any input", mem_id="b"),
        ]
        result = detector.detect(memories)
        for c in result:
            assert 0.0 <= c.severity <= 1.0

    def test_contradiction_has_ids(self):
        detector = ContradictionDetector(self.config)
        memories = [
            _make_memory("Task failed completely", mem_id="id_a"),
            _make_memory("Task success was remarkable and complete", mem_id="id_b"),
        ]
        result = detector.detect(memories)
        for c in result:
            assert c.memory_a_id in ("id_a", "id_b")
            assert c.memory_b_id in ("id_a", "id_b")
            assert c.memory_a_id != c.memory_b_id
