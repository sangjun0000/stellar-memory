"""Emotion analysis for memory items - rule-based with optional LLM."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.config import EmotionConfig, LLMConfig

from stellar_memory.models import EmotionVector

logger = logging.getLogger(__name__)

# Rule-based emotion keyword patterns
EMOTION_KEYWORDS: dict[str, list[str]] = {
    "joy": [
        r"\b(happy|glad|delighted|excited|wonderful|great|amazing|love|enjoy|celebrate|success|win|perfect|fantastic)\b",
        r"(기쁘|행복|좋|즐거|축하|성공|완벽|대박|최고)",
        r"[!]{2,}",
        r"[\U0001F60A\U0001F604\U0001F389\u2764\uFE0F\U0001F44D\U0001F973]",
    ],
    "sadness": [
        r"\b(sad|unhappy|depressed|disappointed|lonely|miss|lost|cry|grief|sorry|regret|fail)\b",
        r"(슬프|우울|실망|외로|그리|잃|아쉬|후회|실패)",
        r"[\U0001F622\U0001F62D\U0001F494]",
    ],
    "anger": [
        r"\b(angry|furious|hate|rage|annoyed|frustrated|irritated|outraged|damn|hell)\b",
        r"(화나|분노|짜증|열받|싫|미치)",
        r"[\U0001F620\U0001F621\U0001F92C]",
    ],
    "fear": [
        r"\b(afraid|scared|terrified|worried|anxious|panic|nervous|threat|danger|risk)\b",
        r"(무서|걱정|불안|공포|위험|두려)",
        r"[\U0001F628\U0001F631\U0001F630]",
    ],
    "surprise": [
        r"\b(surprised|shocked|unexpected|wow|unbelievable|incredible|sudden|astonish)\b",
        r"(놀라|충격|예상.?밖|갑자기|대단|헐)",
        r"[\U0001F62E\U0001F632\U0001F92F]",
    ],
    "disgust": [
        r"\b(disgusting|gross|awful|terrible|horrible|revolting|nasty|creepy)\b",
        r"(역겨|끔찍|최악|혐오|지저분|구역질)",
        r"[\U0001F92E\U0001F637\U0001F922]",
    ],
}


class EmotionAnalyzer:
    """Analyzes text to extract an EmotionVector."""

    def __init__(self, config: EmotionConfig | None = None,
                 llm_config: LLMConfig | None = None):
        from stellar_memory.config import EmotionConfig as _EC
        self._config = config or _EC()
        self._llm_config = llm_config
        self._llm = None

        if self._config.use_llm and llm_config:
            try:
                from stellar_memory.providers import ProviderRegistry
                self._llm = ProviderRegistry.create_llm(llm_config)
            except Exception:
                logger.info("LLM not available for emotion analysis, using rules")

    def analyze(self, text: str) -> EmotionVector:
        """Analyze text and return an EmotionVector."""
        if not self._config.enabled:
            return EmotionVector()

        if self._llm is not None:
            try:
                return self._analyze_llm(text)
            except Exception:
                logger.debug("LLM emotion analysis failed, falling back to rules")

        return self._analyze_rules(text)

    def _analyze_rules(self, text: str) -> EmotionVector:
        """Rule-based emotion analysis using keyword patterns."""
        scores: dict[str, float] = {}
        text_lower = text.lower()

        for emotion, patterns in EMOTION_KEYWORDS.items():
            match_count = sum(
                1 for p in patterns if re.search(p, text_lower)
            )
            scores[emotion] = min(match_count / max(len(patterns), 1), 1.0)

        return EmotionVector(**scores)

    def _analyze_llm(self, text: str) -> EmotionVector:
        """LLM-based emotion analysis."""
        import json

        prompt = (
            "Analyze the emotion of the following text. "
            "Rate each emotion from 0.0 to 1.0:\n"
            "- joy, sadness, anger, fear, surprise, disgust\n\n"
            f"Text: {text[:500]}\n\n"
            "Respond ONLY with JSON: "
            '{"joy": 0.0, "sadness": 0.0, "anger": 0.0, '
            '"fear": 0.0, "surprise": 0.0, "disgust": 0.0}'
        )

        raw = self._llm.complete(prompt, max_tokens=100)
        data = json.loads(raw)
        return EmotionVector.from_dict(data)
