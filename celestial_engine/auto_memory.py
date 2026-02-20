"""대화에서 중요한 정보를 자동 추출하여 저장하는 AutoMemory."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from celestial_engine.importance import ImportanceEvaluator, RuleBasedEvaluator
from celestial_engine.models import CelestialItem

if TYPE_CHECKING:
    from celestial_engine import CelestialMemory


@dataclass
class ExtractedFact:
    """추출된 사실."""

    content: str
    importance: float
    category: str  # "personal" | "factual" | "preference" | "event"


def _text_similarity(a: str, b: str) -> float:
    """간단한 문자열 유사도 (Jaccard similarity on words)."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


class AutoMemory:
    """대화에서 중요한 정보를 자동 추출하여 저장."""

    PERSONAL_PATTERNS = [
        r"(?:my |i am |i'm |i have |내 |제 |나는 )",
        r"(?:name is |이름은 |called )",
    ]
    PREFERENCE_PATTERNS = [
        r"(?:i (?:like|love|prefer|hate|dislike) )",
        r"(?:좋아하|싫어하|선호하)",
        r"(?:favorite |favourite )",
    ]
    EVENT_PATTERNS = [
        r"(?:tomorrow |next |on \w+day |deadline |meeting )",
        r"(?:내일 |다음 |마감 |회의 |약속 )",
    ]

    SIMILARITY_THRESHOLD = 0.85

    def __init__(
        self,
        memory: CelestialMemory,
        evaluator: ImportanceEvaluator | None = None,
        min_importance: float = 0.3,
    ) -> None:
        self._memory = memory
        self._evaluator = evaluator or RuleBasedEvaluator()
        self._min_importance = min_importance

    def process_turn(
        self, user_msg: str, ai_response: str
    ) -> list[CelestialItem]:
        """대화 턴을 분석하여 중요한 사실을 추출 및 저장."""
        facts = self._extract_facts(user_msg, ai_response)
        facts = [f for f in facts if f.importance >= self._min_importance]

        stored: list[CelestialItem] = []
        for fact in facts:
            if not self._is_duplicate(fact.content):
                item = self._memory.store(
                    content=fact.content,
                    importance=fact.importance,
                    metadata={"category": fact.category, "auto": True},
                )
                stored.append(item)

        return stored

    def _extract_facts(
        self, user_msg: str, ai_response: str
    ) -> list[ExtractedFact]:
        """대화에서 저장할 사실 추출."""
        facts: list[ExtractedFact] = []
        sentences = re.split(r"[.!?\n]+", user_msg)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 5:
                continue

            category = self._categorize(sentence)
            importance = self._evaluator.evaluate(sentence)

            if importance >= self._min_importance:
                facts.append(ExtractedFact(
                    content=sentence,
                    importance=importance,
                    category=category,
                ))

        return facts

    def _categorize(self, text: str) -> str:
        """텍스트를 카테고리로 분류."""
        text_lower = text.lower()
        for pattern in self.PERSONAL_PATTERNS:
            if re.search(pattern, text_lower):
                return "personal"
        for pattern in self.PREFERENCE_PATTERNS:
            if re.search(pattern, text_lower):
                return "preference"
        for pattern in self.EVENT_PATTERNS:
            if re.search(pattern, text_lower):
                return "event"
        return "factual"

    def _is_duplicate(self, content: str) -> bool:
        """기존 기억과 유사도 비교하여 중복 판단."""
        existing = self._memory.recall(content, limit=3)
        for item in existing:
            sim = _text_similarity(content, item.content)
            if sim >= self.SIMILARITY_THRESHOLD:
                return True
        return False
