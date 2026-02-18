"""P9-F4: Memory Reasoning - insight derivation and contradiction detection."""

from __future__ import annotations

import logging
import re
from collections import Counter

from stellar_memory.config import ReasoningConfig
from stellar_memory.models import MemoryItem, ReasoningResult, Contradiction

logger = logging.getLogger(__name__)


class MemoryReasoner:
    """Combines memories to derive insights."""

    def __init__(self, config: ReasoningConfig, llm_adapter=None):
        self._config = config
        self._llm = llm_adapter

    def reason(self, query: str, memories: list[MemoryItem],
               graph_neighbors: list[MemoryItem] | None = None) -> ReasoningResult:
        """Reason over memories to derive insights.

        Args:
            query: The reasoning question.
            memories: Recalled memories relevant to query.
            graph_neighbors: Additional memories from graph traversal.
        """
        all_memories = list(memories)
        if graph_neighbors:
            seen_ids = {m.id for m in all_memories}
            for gn in graph_neighbors:
                if gn.id not in seen_ids:
                    all_memories.append(gn)

        all_memories = all_memories[:self._config.max_sources]

        if not all_memories:
            return ReasoningResult(
                query=query,
                source_memories=[],
                insights=["No relevant memories found for reasoning."],
                contradictions=[],
                confidence=0.0,
                reasoning_chain=["No data available"],
            )

        # Derive insights
        if self._llm and self._config.use_llm:
            insights, chain = self._reason_with_llm(query, all_memories)
        else:
            insights, chain = self._reason_without_llm(query, all_memories)

        # Detect contradictions
        contradictions = []
        if self._config.contradiction_check:
            detector = ContradictionDetector(self._config, self._llm)
            contradictions_raw = detector.detect(all_memories)
            contradictions = [
                {"memory_a_id": c.memory_a_id, "memory_b_id": c.memory_b_id,
                 "description": c.description, "severity": c.severity}
                for c in contradictions_raw
            ]

        confidence = self._calculate_confidence(all_memories, insights)

        return ReasoningResult(
            query=query,
            source_memories=all_memories,
            insights=insights,
            contradictions=contradictions,
            confidence=round(confidence, 3),
            reasoning_chain=chain,
        )

    def _reason_with_llm(self, query: str, memories: list[MemoryItem]) -> tuple[list[str], list[str]]:
        """LLM-based reasoning."""
        memory_texts = "\n".join(
            f"{i+1}. {m.content}" for i, m in enumerate(memories)
        )
        prompt = (
            f"Based on the following memories, derive insights about '{query}':\n"
            f"{memory_texts}\n\n"
            f"Provide 1-3 concise insights, each on a new line starting with '- '."
        )
        try:
            response = self._llm.generate(prompt)
            lines = [line.strip().lstrip("- ").strip()
                     for line in response.strip().split("\n")
                     if line.strip() and line.strip().startswith("- ")]
            if not lines:
                lines = [response.strip()]
            chain = [f"LLM reasoning with {len(memories)} sources"]
            return lines, chain
        except Exception as e:
            logger.warning("LLM reasoning failed, falling back to rules: %s", e)
            return self._reason_without_llm(query, memories)

    def _reason_without_llm(self, query: str, memories: list[MemoryItem]) -> tuple[list[str], list[str]]:
        """Rule-based reasoning fallback.

        Finds common keywords between memories and creates connection insights.
        """
        insights: list[str] = []
        chain: list[str] = ["Rule-based reasoning (no LLM)"]

        # Extract keywords from each memory
        keyword_to_memories: dict[str, list[int]] = {}
        for i, m in enumerate(memories):
            words = set(re.findall(r'\b\w{4,}\b', m.content.lower()))
            for w in words:
                if w not in _STOP_WORDS:
                    keyword_to_memories.setdefault(w, []).append(i)

        # Find keywords shared across multiple memories
        shared_keywords = {
            kw: indices for kw, indices in keyword_to_memories.items()
            if len(indices) >= 2
        }

        if shared_keywords:
            # Top 3 shared keywords
            top_shared = sorted(shared_keywords.items(), key=lambda x: -len(x[1]))[:3]
            for kw, indices in top_shared:
                mem_refs = [f"memory {i+1}" for i in indices[:3]]
                insights.append(
                    f"'{kw}' connects {', '.join(mem_refs)} - related theme detected"
                )
                chain.append(f"Shared keyword '{kw}' across {len(indices)} memories")

        # Query keyword matching
        query_words = set(re.findall(r'\b\w{4,}\b', query.lower())) - _STOP_WORDS
        relevant_count = sum(
            1 for m in memories
            if query_words & set(re.findall(r'\b\w{4,}\b', m.content.lower()))
        )

        if relevant_count > 0:
            insights.append(
                f"{relevant_count} of {len(memories)} memories directly mention query terms"
            )
            chain.append(f"Direct keyword overlap: {relevant_count}/{len(memories)}")

        if not insights:
            insights.append(
                f"Found {len(memories)} potentially related memories, "
                f"but no strong connections detected"
            )
            chain.append("No strong keyword overlap found")

        return insights, chain

    def _calculate_confidence(self, memories: list[MemoryItem],
                              insights: list[str]) -> float:
        """Calculate reasoning confidence."""
        if not memories:
            return 0.0

        # More memories = higher confidence (saturates at max_sources)
        memory_factor = min(len(memories) / self._config.max_sources, 1.0)

        # More insights = higher confidence (saturates at 3)
        insight_factor = min(len(insights) / 3.0, 1.0)

        # Lower zones = higher confidence
        avg_zone = sum(m.zone for m in memories if m.zone >= 0) / max(
            sum(1 for m in memories if m.zone >= 0), 1
        )
        zone_factor = max(0.0, 1.0 - (avg_zone / 4.0))

        return 0.3 * memory_factor + 0.3 * insight_factor + 0.4 * zone_factor


class ContradictionDetector:
    """Detects contradictions between memories."""

    def __init__(self, config: ReasoningConfig, llm_adapter=None):
        self._config = config
        self._llm = llm_adapter

    def detect(self, memories: list[MemoryItem]) -> list[Contradiction]:
        """Detect contradictions among memory pairs."""
        if len(memories) < 2:
            return []

        contradictions: list[Contradiction] = []
        checked = set()

        for i, mem_a in enumerate(memories):
            for j, mem_b in enumerate(memories):
                if i >= j:
                    continue
                pair_key = (mem_a.id, mem_b.id)
                if pair_key in checked:
                    continue
                checked.add(pair_key)

                if self._llm and self._config.use_llm:
                    result = self._detect_with_llm(mem_a, mem_b)
                else:
                    result = self._detect_with_rules(mem_a, mem_b)

                if result:
                    contradictions.append(result)

        return contradictions

    def _detect_with_llm(self, mem_a: MemoryItem, mem_b: MemoryItem) -> Contradiction | None:
        """LLM-based contradiction detection."""
        prompt = (
            f"Do these two statements contradict each other?\n"
            f"A: {mem_a.content}\n"
            f"B: {mem_b.content}\n\n"
            f"Answer 'YES: <explanation>' or 'NO'."
        )
        try:
            response = self._llm.generate(prompt).strip()
            if response.upper().startswith("YES"):
                desc = response[4:].strip().lstrip(":").strip() or "Contradiction detected by LLM"
                return Contradiction(
                    memory_a_id=mem_a.id,
                    memory_b_id=mem_b.id,
                    description=desc,
                    severity=0.7,
                )
        except Exception as e:
            logger.warning("LLM contradiction check failed: %s", e)
            return self._detect_with_rules(mem_a, mem_b)
        return None

    def _detect_with_rules(self, mem_a: MemoryItem, mem_b: MemoryItem) -> Contradiction | None:
        """Rule-based contradiction detection.

        Looks for negation patterns on the same subject.
        """
        a_lower = mem_a.content.lower()
        b_lower = mem_b.content.lower()

        # Find common significant words
        words_a = set(re.findall(r'\b\w{4,}\b', a_lower)) - _STOP_WORDS
        words_b = set(re.findall(r'\b\w{4,}\b', b_lower)) - _STOP_WORDS
        common = words_a & words_b

        if not common:
            return None

        # Check negation patterns
        negation_patterns = [
            (r'\bnot\b', r'\bis\b'),
            (r'\bnever\b', r'\balways\b'),
            (r'\bno\b', r'\byes\b'),
            (r'\bfalse\b', r'\btrue\b'),
            (r'\bwrong\b', r'\bright\b'),
            (r'\bfail\b', r'\bsuccess\b'),
            (r'\bbad\b', r'\bgood\b'),
        ]

        a_has_neg = any(re.search(p[0], a_lower) for p in negation_patterns)
        b_has_neg = any(re.search(p[0], b_lower) for p in negation_patterns)

        # One has negation and the other doesn't, with common subject
        if (a_has_neg != b_has_neg) and len(common) >= 2:
            shared = ", ".join(list(common)[:3])
            return Contradiction(
                memory_a_id=mem_a.id,
                memory_b_id=mem_b.id,
                description=f"Potential contradiction on '{shared}' (negation pattern)",
                severity=0.5,
            )

        # Check antonym pairs in same subject context
        for pos, neg in negation_patterns:
            if re.search(pos, a_lower) and re.search(neg, b_lower):
                return Contradiction(
                    memory_a_id=mem_a.id,
                    memory_b_id=mem_b.id,
                    description=f"Antonym pattern detected with shared context: {', '.join(list(common)[:3])}",
                    severity=0.4,
                )

        return None


# Common stop words to ignore in analysis
_STOP_WORDS = frozenset({
    "that", "this", "with", "from", "have", "been", "were", "they",
    "their", "which", "about", "would", "there", "could", "other",
    "into", "more", "some", "than", "them", "very", "when", "what",
    "your", "each", "make", "like", "just", "over", "such", "also",
    "back", "after", "only", "most", "even", "made", "many",
})
