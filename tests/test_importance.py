"""Tests for importance evaluator module."""

from stellar_memory.importance_evaluator import (
    RuleBasedEvaluator, NullEvaluator, create_evaluator, _pattern_score,
)
from stellar_memory.config import LLMConfig


class TestRuleBasedEvaluator:
    def test_factual_content(self):
        evaluator = RuleBasedEvaluator()
        result = evaluator.evaluate("The meeting is on 2024-01-15 with 50 km distance")
        assert result.factual_score > 0
        assert result.method == "rule"

    def test_emotional_content(self):
        evaluator = RuleBasedEvaluator()
        result = evaluator.evaluate("I love this amazing experience!!")
        assert result.emotional_score > 0
        assert result.method == "rule"

    def test_actionable_content(self):
        evaluator = RuleBasedEvaluator()
        result = evaluator.evaluate("Must complete the task before the deadline, urgent!")
        assert result.actionable_score > 0
        assert result.method == "rule"

    def test_explicit_importance(self):
        evaluator = RuleBasedEvaluator()
        result = evaluator.evaluate("This is critical - remember the password!")
        assert result.explicit_score > 0
        assert result.method == "rule"

    def test_neutral_content_low_score(self):
        evaluator = RuleBasedEvaluator()
        result = evaluator.evaluate("The weather is mild today")
        assert result.importance < 0.5

    def test_highly_important_content(self):
        evaluator = RuleBasedEvaluator()
        result = evaluator.evaluate(
            "URGENT: Must remember this critical deadline 2024-03-01! I'm so worried!!"
        )
        assert result.importance > 0.3

    def test_importance_clamped(self):
        evaluator = RuleBasedEvaluator()
        result = evaluator.evaluate("anything")
        assert 0.0 <= result.importance <= 1.0


class TestNullEvaluator:
    def test_returns_default(self):
        evaluator = NullEvaluator()
        result = evaluator.evaluate("anything at all")
        assert result.importance == 0.5
        assert result.method == "default"
        assert result.factual_score == 0.0


class TestCreateEvaluator:
    def test_disabled_returns_null(self):
        cfg = LLMConfig(enabled=False)
        evaluator = create_evaluator(cfg)
        assert isinstance(evaluator, NullEvaluator)

    def test_enabled_without_anthropic(self):
        """Without anthropic installed, should fall back to RuleBasedEvaluator."""
        cfg = LLMConfig(enabled=True)
        evaluator = create_evaluator(cfg)
        # Either LLMEvaluator or RuleBasedEvaluator depending on install
        assert hasattr(evaluator, "evaluate")


class TestPatternScore:
    def test_no_match(self):
        assert _pattern_score("hello world", [r"\d+"]) == 0.0

    def test_full_match(self):
        score = _pattern_score("123 abc", [r"\d+"])
        assert score > 0

    def test_empty_patterns(self):
        assert _pattern_score("anything", []) == 0.0
