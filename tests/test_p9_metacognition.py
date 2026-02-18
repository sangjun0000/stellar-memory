"""Tests for P9-F1: Metacognition Engine."""

import time
import pytest

from stellar_memory.config import MetacognitionConfig
from stellar_memory.metacognition import Introspector, ConfidenceScorer
from stellar_memory.models import MemoryItem, IntrospectionResult, ConfidentRecall


def _make_memory(content: str, zone: int = 0, tags: list[str] | None = None,
                 total_score: float = 0.5, recall_offset: float = 0.0) -> MemoryItem:
    now = time.time()
    return MemoryItem(
        id=f"mem_{hash(content) % 10000}",
        content=content,
        created_at=now - 3600,
        last_recalled_at=now - recall_offset,
        recall_count=1,
        arbitrary_importance=0.5,
        zone=zone,
        metadata={"tags": tags or []},
        total_score=total_score,
    )


class TestIntrospector:
    def setup_method(self):
        self.config = MetacognitionConfig(enabled=True)
        self.introspector = Introspector(self.config)

    def test_introspect_empty_memories(self):
        result = self.introspector.introspect("Python", [])
        assert result.confidence == 0.0
        assert result.gaps == ["Python"]
        assert result.memory_count == 0
        assert result.coverage == []

    def test_introspect_with_memories(self):
        memories = [
            _make_memory("Python is a great programming language", tags=["python", "programming"]),
            _make_memory("Django framework for web development", tags=["django", "web"]),
        ]
        result = self.introspector.introspect("Python", memories)
        assert result.confidence > 0.0
        assert result.memory_count == 2
        assert len(result.coverage) > 0

    def test_introspect_confidence_range(self):
        memories = [_make_memory(f"Memory about topic {i}", tags=["topic"]) for i in range(15)]
        result = self.introspector.introspect("topic", memories)
        assert 0.0 <= result.confidence <= 1.0

    def test_introspect_topic_field(self):
        result = self.introspector.introspect("React", [])
        assert result.topic == "React"

    def test_introspect_gaps_from_graph_neighbors(self):
        memories = [_make_memory("Python basics", tags=["python"])]
        neighbors = ["django", "flask", "fastapi"]
        result = self.introspector.introspect(
            "Python", memories, graph_neighbors=neighbors
        )
        # django/flask/fastapi should appear as gaps since they aren't in coverage
        assert len(result.gaps) > 0

    def test_introspect_no_gaps_when_covered(self):
        memories = [
            _make_memory("Django is excellent for web development", tags=["django"]),
        ]
        neighbors = ["django"]
        result = self.introspector.introspect(
            "web", memories, graph_neighbors=neighbors
        )
        # "django" is in coverage so not a gap
        assert "django" not in result.gaps

    def test_introspect_zone_distribution(self):
        memories = [
            _make_memory("Core memory", zone=0),
            _make_memory("Inner memory", zone=1),
            _make_memory("Another inner memory", zone=1),
        ]
        result = self.introspector.introspect("test", memories)
        assert result.zone_distribution[0] == 1
        assert result.zone_distribution[1] == 2

    def test_introspect_freshness(self):
        fresh = _make_memory("Fresh memory", recall_offset=0)
        stale = _make_memory("Old memory", recall_offset=90000)  # > 1 day
        result_fresh = self.introspector.introspect("test", [fresh])
        result_stale = self.introspector.introspect("test", [stale])
        assert result_fresh.avg_freshness > result_stale.avg_freshness

    def test_introspect_confidence_increases_with_more_memories(self):
        few = [_make_memory(f"Memory {i}", tags=["topic"]) for i in range(2)]
        many = [_make_memory(f"Memory {i}", tags=["topic"]) for i in range(10)]
        r_few = self.introspector.introspect("topic", few)
        r_many = self.introspector.introspect("topic", many)
        assert r_many.confidence >= r_few.confidence

    def test_coverage_extracts_tags(self):
        memories = [
            _make_memory("content", tags=["python", "coding"]),
        ]
        result = self.introspector.introspect("test", memories)
        assert "python" in result.coverage
        assert "coding" in result.coverage

    def test_coverage_extracts_keywords(self):
        memories = [
            _make_memory("Programming language features overview"),
        ]
        result = self.introspector.introspect("test", memories)
        # Words > 4 chars should be in coverage
        assert any("programming" in c.lower() for c in result.coverage)


class TestConfidenceScorer:
    def setup_method(self):
        self.config = MetacognitionConfig(
            enabled=True,
            low_confidence_threshold=0.3,
        )
        self.scorer = ConfidenceScorer(self.config)

    def test_score_empty(self):
        result = self.scorer.score([], "test")
        assert result.confidence == 0.0
        assert result.warning is not None
        assert result.memories == []

    def test_score_with_memories(self):
        memories = [
            _make_memory("Python basics", zone=0, total_score=0.8),
            _make_memory("Python advanced", zone=1, total_score=0.6),
        ]
        result = self.scorer.score(memories, "Python")
        assert 0.0 < result.confidence <= 1.0
        assert len(result.memories) == 2

    def test_low_confidence_warning(self):
        memories = [
            _make_memory("Vague memory", zone=3, total_score=0.1),
        ]
        result = self.scorer.score(memories, "obscure topic")
        if result.confidence < 0.3:
            assert result.warning is not None

    def test_high_confidence_no_warning(self):
        memories = [
            _make_memory(f"Core memory {i}", zone=0, total_score=0.9)
            for i in range(10)
        ]
        result = self.scorer.score(memories, "well-known topic")
        # With 10 core memories and high scores, confidence should be high
        assert result.confidence > 0.5
        assert result.warning is None

    def test_core_zone_higher_confidence(self):
        core = [_make_memory("Core", zone=0, total_score=0.5)]
        belt = [_make_memory("Belt", zone=3, total_score=0.5)]
        r_core = self.scorer.score(core, "test")
        r_belt = self.scorer.score(belt, "test")
        assert r_core.confidence >= r_belt.confidence

    def test_more_results_higher_confidence(self):
        few = [_make_memory(f"Mem {i}", zone=1, total_score=0.5) for i in range(2)]
        many = [_make_memory(f"Mem {i}", zone=1, total_score=0.5) for i in range(10)]
        r_few = self.scorer.score(few, "test")
        r_many = self.scorer.score(many, "test")
        assert r_many.confidence >= r_few.confidence

    def test_higher_scores_higher_confidence(self):
        low = [_make_memory("Low", zone=1, total_score=0.1)]
        high = [_make_memory("High", zone=1, total_score=0.9)]
        r_low = self.scorer.score(low, "test")
        r_high = self.scorer.score(high, "test")
        assert r_high.confidence >= r_low.confidence

    def test_confidence_clamped(self):
        memories = [
            _make_memory(f"Mem {i}", zone=0, total_score=1.0)
            for i in range(20)
        ]
        result = self.scorer.score(memories, "test")
        assert result.confidence <= 1.0
        assert result.confidence >= 0.0
