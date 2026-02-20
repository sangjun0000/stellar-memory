"""Importance evaluator for arbitrary importance A(m) scoring."""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ImportanceEvaluator(ABC):
    """Abstract importance evaluator interface."""

    @abstractmethod
    def evaluate(self, content: str) -> float:
        """Evaluate content importance, returns [0.0, 1.0]."""
        ...


class DefaultEvaluator(ImportanceEvaluator):
    """Default evaluator: always returns 0.5."""

    def evaluate(self, content: str) -> float:
        return 0.5


class RuleBasedEvaluator(ImportanceEvaluator):
    """Rule-based evaluator using keyword pattern matching."""

    FACTUAL_PATTERNS = [
        r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",
        r"\b\d+\s*(kg|km|m|cm|mm|gb|mb|tb|%)\b",
        r"\b(fact|data|statistic|number|result)\b",
    ]
    EMOTIONAL_PATTERNS = [
        r"\b(love|hate|happy|sad|angry|fear|joy|excited|worried)\b",
        r"\b(amazing|terrible|wonderful|horrible|fantastic|awful)\b",
    ]
    ACTIONABLE_PATTERNS = [
        r"\b(todo|must|should|need to|have to|deadline|urgent|asap)\b",
        r"\b(schedule|meeting|appointment|task|action item)\b",
    ]
    EXPLICIT_PATTERNS = [
        r"\b(important|critical|remember|never forget|key|essential)\b",
        r"\b(password|secret|api.?key|token|credential)\b",
    ]

    def evaluate(self, content: str) -> float:
        text = content.lower()
        f = self._score(text, self.FACTUAL_PATTERNS)
        e = self._score(text, self.EMOTIONAL_PATTERNS)
        a = self._score(text, self.ACTIONABLE_PATTERNS)
        x = self._score(text, self.EXPLICIT_PATTERNS)
        return max(0.0, min(1.0, 0.25 * f + 0.25 * e + 0.30 * a + 0.20 * x))

    def _score(self, text: str, patterns: list[str]) -> float:
        matches = sum(1 for p in patterns if re.search(p, text))
        return min(matches / max(len(patterns), 1), 1.0)


class LLMEvaluator(ImportanceEvaluator):
    """LLM-based evaluator: AI autonomously judges importance.

    Accepts a callable ``llm_callable(prompt: str) -> str`` for LLM access.
    Falls back to RuleBasedEvaluator on failure.
    """

    def __init__(self, llm_callable=None) -> None:
        self._llm = llm_callable
        self._fallback = RuleBasedEvaluator()

    def evaluate(self, content: str) -> float:
        if self._llm is None:
            return self._fallback.evaluate(content)
        try:
            return self._call_llm(content)
        except Exception as exc:
            logger.warning("LLM evaluation failed: %s, falling back to rules", exc)
            return self._fallback.evaluate(content)

    def _call_llm(self, content: str) -> float:
        import json

        prompt = (
            "Rate the importance of this memory on a scale of 0.0 to 1.0.\n"
            "Consider: factual value, emotional significance, actionability, "
            "and explicit importance markers.\n\n"
            f"Memory: {content}\n\n"
            'Respond ONLY with JSON: {"importance": 0.0}'
        )
        raw = self._llm(prompt)
        data = json.loads(raw)
        return max(0.0, min(1.0, float(data.get("importance", 0.5))))
