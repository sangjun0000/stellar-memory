"""Importance evaluator for memory items - rule-based with optional LLM fallback."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.config import LLMConfig

from stellar_memory.models import EvaluationResult

logger = logging.getLogger(__name__)

# Rule-based keyword patterns (English + Korean)
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
    r"(내일|tomorrow|다음\s*주|next week)",
    r"(미팅|meeting|약속|appointment|회의)",
    r"(해야|must|should|need to|할\s*일|todo)",
]
EXPLICIT_KEYWORDS = [
    r"\b(important|critical|remember|never forget|key|essential|vital)\b",
    r"\b(password|secret|api.?key|token|credential)\b",
    r"(기억해|remember|잊지\s*마|don't forget)",
    r"(중요|important|critical|urgent)",
]
LOW_IMPORTANCE_PATTERNS = [
    (r"^(네|예|응|ㅇㅇ|ok|sure|alright)$", 0.1),
    (r"^(ㅋ+|ㅎ+|lol|haha)$", 0.05),
]


def _pattern_score(text: str, patterns: list[str]) -> float:
    text_lower = text.lower()
    matches = sum(1 for p in patterns if re.search(p, text_lower))
    return min(matches / max(len(patterns), 1), 1.0)


class RuleBasedEvaluator:
    """Evaluate importance using keyword pattern matching."""

    CRITERIA_WEIGHTS = {
        "factual": 0.3,
        "emotional": 0.2,
        "actionable": 0.3,
        "explicit": 0.2,
    }

    def evaluate(self, content: str) -> EvaluationResult:
        # Check low-importance patterns first (short-circuit)
        stripped = content.strip()
        for pattern, score in LOW_IMPORTANCE_PATTERNS:
            if re.search(pattern, stripped, re.IGNORECASE):
                return EvaluationResult(
                    importance=score,
                    factual_score=0.1,
                    emotional_score=0.1,
                    actionable_score=0.1,
                    explicit_score=0.0,
                    method="rule",
                )

        factual = _pattern_score(content, FACTUAL_PATTERNS)
        emotional = _pattern_score(content, EMOTIONAL_PATTERNS)
        actionable = _pattern_score(content, ACTIONABLE_PATTERNS)
        explicit = _pattern_score(content, EXPLICIT_KEYWORDS)

        importance = (
            self.CRITERIA_WEIGHTS["factual"] * factual
            + self.CRITERIA_WEIGHTS["emotional"] * emotional
            + self.CRITERIA_WEIGHTS["actionable"] * actionable
            + self.CRITERIA_WEIGHTS["explicit"] * explicit
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

    CRITERIA_WEIGHTS = {
        "factual": 0.3,
        "emotional": 0.2,
        "actionable": 0.3,
        "explicit": 0.2,
    }

    def _call_llm(self, content: str) -> EvaluationResult:
        import json
        prompt = (
            "Evaluate the importance of this memory on a scale of 0.0 to 1.0.\n\n"
            f'Memory: "{content}"\n\n'
            "Rate each criterion (0.0-1.0):\n"
            "- factual: Contains facts, names, dates, rules, numbers\n"
            "- emotional: Related to emotions, feelings, personal matters\n"
            "- actionable: Contains tasks, appointments, deadlines, commitments\n"
            "- explicit: User explicitly asked to remember this\n\n"
            "Respond in JSON only:\n"
            '{"factual": 0.0, "emotional": 0.0, "actionable": 0.0, "explicit": 0.0}'
        )

        from stellar_memory.providers import ProviderRegistry
        llm = ProviderRegistry.create_llm(self._config)
        raw = llm.complete(prompt, self._config.max_tokens)

        # Extract JSON from response (handles markdown code blocks)
        match = re.search(r'\{[^}]+\}', raw)
        if not match:
            raise ValueError("No JSON found in LLM response")
        scores = json.loads(match.group())

        factual = max(0.0, min(1.0, float(scores.get("factual", 0.5))))
        emotional = max(0.0, min(1.0, float(scores.get("emotional", 0.5))))
        actionable = max(0.0, min(1.0, float(scores.get("actionable", 0.5))))
        explicit = max(0.0, min(1.0, float(scores.get("explicit", 0.5))))

        importance = sum(
            scores_val * self.CRITERIA_WEIGHTS[k]
            for k, scores_val in [
                ("factual", factual), ("emotional", emotional),
                ("actionable", actionable), ("explicit", explicit),
            ]
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
            factual_score=0.5,
            emotional_score=0.5,
            actionable_score=0.5,
            explicit_score=0.5,
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
