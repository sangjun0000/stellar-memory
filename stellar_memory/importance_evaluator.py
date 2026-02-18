"""Importance evaluator for memory items - rule-based with optional LLM fallback."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.config import LLMConfig

from stellar_memory.models import EvaluationResult

logger = logging.getLogger(__name__)

# Rule-based keyword patterns
FACTUAL_PATTERNS = [
    r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",  # dates
    r"\b\d+\s*(kg|km|m|cm|mm|gb|mb|tb|%)\b",  # measurements
    r"\b(fact|data|statistic|number|result)\b",
]
EMOTIONAL_PATTERNS = [
    r"\b(love|hate|happy|sad|angry|fear|joy|excited|worried|grateful)\b",
    r"\b(amazing|terrible|wonderful|horrible|fantastic|awful)\b",
    r"[!?]{2,}",  # multiple punctuation
]
ACTIONABLE_PATTERNS = [
    r"\b(todo|must|should|need to|have to|deadline|urgent|asap|reminder)\b",
    r"\b(schedule|meeting|appointment|task|action item)\b",
]
EXPLICIT_KEYWORDS = [
    r"\b(important|critical|remember|never forget|key|essential|vital)\b",
    r"\b(password|secret|api.?key|token|credential)\b",
]


def _pattern_score(text: str, patterns: list[str]) -> float:
    text_lower = text.lower()
    matches = sum(1 for p in patterns if re.search(p, text_lower))
    return min(matches / max(len(patterns), 1), 1.0)


class RuleBasedEvaluator:
    """Evaluate importance using keyword pattern matching."""

    def evaluate(self, content: str) -> EvaluationResult:
        factual = _pattern_score(content, FACTUAL_PATTERNS)
        emotional = _pattern_score(content, EMOTIONAL_PATTERNS)
        actionable = _pattern_score(content, ACTIONABLE_PATTERNS)
        explicit = _pattern_score(content, EXPLICIT_KEYWORDS)

        importance = (
            0.25 * factual
            + 0.25 * emotional
            + 0.30 * actionable
            + 0.20 * explicit
        )
        importance = max(0.0, min(1.0, importance))

        return EvaluationResult(
            importance=importance,
            factual_score=factual,
            emotional_score=emotional,
            actionable_score=actionable,
            explicit_score=explicit,
            method="rule",
        )


class LLMEvaluator:
    """Evaluate importance using LLM API calls."""

    def __init__(self, config: LLMConfig | None = None):
        from stellar_memory.config import LLMConfig as _LC
        self._config = config or _LC()

    def evaluate(self, content: str) -> EvaluationResult:
        try:
            return self._call_llm(content)
        except Exception as e:
            logger.warning("LLM evaluation failed: %s, falling back to rules", e)
            return RuleBasedEvaluator().evaluate(content)

    def _call_llm(self, content: str) -> EvaluationResult:
        import json
        prompt = (
            "Rate the following text on 4 dimensions (0.0 to 1.0):\n"
            "- factual: contains facts, data, or specific information\n"
            "- emotional: has emotional significance\n"
            "- actionable: requires action or has a deadline\n"
            "- explicit: explicitly marked as important\n\n"
            f"Text: {content}\n\n"
            "Respond ONLY with JSON: "
            '{"factual": 0.0, "emotional": 0.0, "actionable": 0.0, "explicit": 0.0}'
        )

        from stellar_memory.providers import ProviderRegistry
        llm = ProviderRegistry.create_llm(self._config)
        raw = llm.complete(prompt, self._config.max_tokens)

        scores = json.loads(raw)
        factual = float(scores.get("factual", 0.0))
        emotional = float(scores.get("emotional", 0.0))
        actionable = float(scores.get("actionable", 0.0))
        explicit = float(scores.get("explicit", 0.0))

        importance = (
            0.25 * factual + 0.25 * emotional + 0.30 * actionable + 0.20 * explicit
        )
        return EvaluationResult(
            importance=max(0.0, min(1.0, importance)),
            factual_score=factual,
            emotional_score=emotional,
            actionable_score=actionable,
            explicit_score=explicit,
            method="llm",
        )


class NullEvaluator:
    """Fallback when evaluation is disabled."""

    def evaluate(self, content: str) -> EvaluationResult:
        return EvaluationResult(
            importance=0.5,
            factual_score=0.0,
            emotional_score=0.0,
            actionable_score=0.0,
            explicit_score=0.0,
            method="default",
        )


def create_evaluator(
    config: LLMConfig | None = None,
) -> RuleBasedEvaluator | LLMEvaluator | NullEvaluator:
    """Create an importance evaluator with graceful degradation."""
    from stellar_memory.config import LLMConfig as _LC
    cfg = config or _LC()
    if not cfg.enabled:
        return NullEvaluator()
    try:
        from stellar_memory.providers import ProviderRegistry
        ProviderRegistry.create_llm(cfg)  # verify provider is available
        return LLMEvaluator(cfg)
    except Exception:
        logger.info("LLM provider not available, using RuleBasedEvaluator")
        return RuleBasedEvaluator()
