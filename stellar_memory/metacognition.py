"""P9-F1: Metacognition Engine - self-awareness of knowledge state."""

from __future__ import annotations

import time
from collections import Counter

from stellar_memory.config import MetacognitionConfig
from stellar_memory.models import IntrospectionResult, ConfidentRecall, MemoryItem


class Introspector:
    """Analyzes knowledge state for a given topic."""

    def __init__(self, config: MetacognitionConfig):
        self._config = config

    def introspect(self, topic: str, memories: list[MemoryItem],
                   graph_neighbors: list[str] | None = None,
                   current_time: float | None = None) -> IntrospectionResult:
        if current_time is None:
            current_time = time.time()

        if not memories:
            return IntrospectionResult(
                topic=topic,
                confidence=0.0,
                coverage=[],
                gaps=[topic],
                memory_count=0,
                avg_freshness=0.0,
                zone_distribution={},
            )

        # Coverage: unique tags/keywords from memories
        coverage = self._extract_coverage(memories)

        # Gaps: graph neighbors not in coverage
        gaps = []
        if graph_neighbors:
            coverage_lower = {c.lower() for c in coverage}
            gaps = [n for n in graph_neighbors if n.lower() not in coverage_lower]

        # Zone distribution
        zone_dist: dict[int, int] = {}
        for m in memories:
            zone_dist[m.zone] = zone_dist.get(m.zone, 0) + 1

        # Average freshness (normalized 0~1)
        freshness_values = []
        for m in memories:
            delta = current_time - m.last_recalled_at
            f = max(0.0, 1.0 - (delta / 86400))  # 1 day = 0 freshness
            freshness_values.append(max(0.0, min(1.0, f)))
        avg_freshness = sum(freshness_values) / len(freshness_values) if freshness_values else 0.0

        # Confidence calculation
        confidence = self._calculate_confidence(
            memories, coverage, avg_freshness
        )

        return IntrospectionResult(
            topic=topic,
            confidence=round(confidence, 3),
            coverage=coverage,
            gaps=gaps,
            memory_count=len(memories),
            avg_freshness=round(avg_freshness, 3),
            zone_distribution=zone_dist,
        )

    def _extract_coverage(self, memories: list[MemoryItem]) -> list[str]:
        """Extract unique subtopics from memory tags and content keywords."""
        tags: set[str] = set()
        for m in memories:
            if m.metadata and "tags" in m.metadata:
                for t in m.metadata["tags"]:
                    tags.add(t)
            # Extract significant words from content (>4 chars, not common)
            words = m.content.lower().split()
            for w in words:
                cleaned = w.strip(".,!?;:'\"()[]{}").strip()
                if len(cleaned) > 4 and cleaned.isalpha():
                    tags.add(cleaned)
        # Limit to top 20 by frequency
        counter = Counter()
        for m in memories:
            words = m.content.lower().split()
            for w in words:
                cleaned = w.strip(".,!?;:'\"()[]{}").strip()
                if len(cleaned) > 4 and cleaned.isalpha():
                    counter[cleaned] += 1
        top_words = [w for w, _ in counter.most_common(20)]
        # Merge tags
        all_tags = list(tags)
        for w in top_words:
            if w not in all_tags:
                all_tags.append(w)
        return all_tags[:30]

    def _calculate_confidence(self, memories: list[MemoryItem],
                              coverage: list[str],
                              avg_freshness: float) -> float:
        """confidence = α*coverage_ratio + β*avg_freshness + γ*memory_density"""
        a = self._config.confidence_alpha
        b = self._config.confidence_beta
        g = self._config.confidence_gamma

        coverage_ratio = min(len(coverage) / 10, 1.0) if coverage else 0.0
        memory_density = min(len(memories) / 10, 1.0)

        return min(1.0, a * coverage_ratio + b * avg_freshness + g * memory_density)


class ConfidenceScorer:
    """Scores recall result confidence."""

    def __init__(self, config: MetacognitionConfig):
        self._config = config

    def score(self, memories: list[MemoryItem], query: str) -> ConfidentRecall:
        if not memories:
            return ConfidentRecall(
                memories=[],
                confidence=0.0,
                warning=f"No memories found for '{query}'",
            )

        # Factor 1: result count (saturates at 10)
        count_factor = min(len(memories) / 10, 1.0)

        # Factor 2: average zone (lower = more core = higher confidence)
        avg_zone = sum(m.zone for m in memories if m.zone >= 0) / max(
            sum(1 for m in memories if m.zone >= 0), 1
        )
        zone_factor = max(0.0, 1.0 - (avg_zone / 4))  # zone 0=1.0, zone 4=0.0

        # Factor 3: average total score
        avg_score = sum(m.total_score for m in memories) / len(memories)
        score_factor = min(avg_score, 1.0)

        confidence = (0.3 * count_factor + 0.4 * zone_factor + 0.3 * score_factor)
        confidence = round(min(1.0, max(0.0, confidence)), 3)

        warning = None
        if confidence < self._config.low_confidence_threshold:
            warning = f"Low confidence ({confidence:.2f}) - limited knowledge on this topic"

        return ConfidentRecall(
            memories=memories,
            confidence=confidence,
            warning=warning,
        )
