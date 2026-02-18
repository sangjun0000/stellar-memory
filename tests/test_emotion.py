"""Tests for P7 emotion module: EmotionVector, EmotionAnalyzer, memory function integration."""

import time
import pytest

from stellar_memory.models import EmotionVector, MemoryItem, ScoreBreakdown
from stellar_memory.emotion import EmotionAnalyzer, EMOTION_KEYWORDS
from stellar_memory.config import EmotionConfig, MemoryFunctionConfig
from stellar_memory.memory_function import MemoryFunction


class TestEmotionVector:
    def test_creation_defaults(self):
        ev = EmotionVector()
        assert ev.joy == 0.0
        assert ev.intensity == 0.0
        assert ev.dominant == "joy"  # all zero, first in dict

    def test_intensity(self):
        ev = EmotionVector(joy=0.8, sadness=0.2)
        assert ev.intensity == 0.8

    def test_dominant(self):
        ev = EmotionVector(anger=0.9, joy=0.1)
        assert ev.dominant == "anger"

    def test_to_from_dict(self):
        ev = EmotionVector(joy=0.5, fear=0.3, surprise=0.7)
        d = ev.to_dict()
        assert d["joy"] == 0.5
        assert d["surprise"] == 0.7
        restored = EmotionVector.from_dict(d)
        assert restored.joy == 0.5
        assert restored.surprise == 0.7

    def test_to_from_list(self):
        ev = EmotionVector(joy=0.1, sadness=0.2, anger=0.3,
                           fear=0.4, surprise=0.5, disgust=0.6)
        lst = ev.to_list()
        assert len(lst) == 6
        assert lst == [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
        restored = EmotionVector.from_list(lst)
        assert restored.disgust == 0.6

    def test_from_dict_missing_keys(self):
        ev = EmotionVector.from_dict({"joy": 0.5})
        assert ev.joy == 0.5
        assert ev.sadness == 0.0


class TestEmotionAnalyzer:
    def test_disabled(self):
        analyzer = EmotionAnalyzer(EmotionConfig(enabled=False))
        ev = analyzer.analyze("I am so happy!!")
        assert ev.intensity == 0.0

    def test_rule_joy(self):
        analyzer = EmotionAnalyzer(EmotionConfig(enabled=True))
        ev = analyzer.analyze("I am so happy and excited!! This is amazing!")
        assert ev.joy > 0.0

    def test_rule_sadness(self):
        analyzer = EmotionAnalyzer(EmotionConfig(enabled=True))
        ev = analyzer.analyze("I feel so sad and disappointed, full of regret")
        assert ev.sadness > 0.0

    def test_rule_anger(self):
        analyzer = EmotionAnalyzer(EmotionConfig(enabled=True))
        ev = analyzer.analyze("I am furious and angry about this outraged situation")
        assert ev.anger > 0.0

    def test_rule_fear(self):
        analyzer = EmotionAnalyzer(EmotionConfig(enabled=True))
        ev = analyzer.analyze("I am scared and terrified, feeling anxious about the danger")
        assert ev.fear > 0.0

    def test_rule_surprise(self):
        analyzer = EmotionAnalyzer(EmotionConfig(enabled=True))
        ev = analyzer.analyze("I was shocked and surprised by the unexpected news, wow!")
        assert ev.surprise > 0.0

    def test_rule_neutral(self):
        analyzer = EmotionAnalyzer(EmotionConfig(enabled=True))
        ev = analyzer.analyze("The function returns an integer value")
        assert ev.intensity < 0.5

    def test_korean_emotion(self):
        analyzer = EmotionAnalyzer(EmotionConfig(enabled=True))
        ev = analyzer.analyze("정말 행복하고 즐거운 하루였어요!")
        assert ev.joy > 0.0

    def test_exclamation_marks(self):
        analyzer = EmotionAnalyzer(EmotionConfig(enabled=True))
        ev = analyzer.analyze("Wow!! This is incredible!!")
        assert ev.joy > 0.0  # "!!" matches joy pattern


class TestMemoryFunctionEmotion:
    def test_emotion_score_none(self):
        mf = MemoryFunction()
        item = MemoryItem.create("test")
        assert item.emotion is None
        now = time.time()
        breakdown = mf.calculate(item, now)
        assert breakdown.emotion_score == 0.0

    def test_emotion_score_with_emotion(self):
        cfg = MemoryFunctionConfig(w_emotion=0.15)
        mf = MemoryFunction(cfg)
        item = MemoryItem.create("test")
        item.emotion = EmotionVector(joy=0.9)
        now = time.time()
        breakdown = mf.calculate(item, now)
        assert breakdown.emotion_score == 0.9
        # Total should include emotion contribution
        assert breakdown.total > 0

    def test_score_breakdown_has_emotion(self):
        mf = MemoryFunction()
        item = MemoryItem.create("test")
        now = time.time()
        breakdown = mf.calculate(item, now)
        assert hasattr(breakdown, "emotion_score")

    def test_backward_compat_w_emotion_zero(self):
        """w_emotion=0.0 means emotion has no effect."""
        cfg = MemoryFunctionConfig(w_emotion=0.0)
        mf = MemoryFunction(cfg)
        item = MemoryItem.create("test", importance=0.5)
        item.emotion = EmotionVector(joy=1.0)
        now = item.created_at
        breakdown = mf.calculate(item, now)
        # With w_emotion=0, emotion shouldn't affect total
        item2 = MemoryItem.create("test", importance=0.5)
        item2.created_at = item.created_at
        item2.last_recalled_at = item.last_recalled_at
        breakdown2 = mf.calculate(item2, now)
        assert abs(breakdown.total - breakdown2.total) < 0.001


class TestStellarMemoryEmotion:
    def test_store_with_explicit_emotion(self):
        from stellar_memory import StellarMemory, StellarConfig
        config = StellarConfig(db_path=":memory:")
        mem = StellarMemory(config)
        ev = EmotionVector(joy=0.8, surprise=0.5)
        item = mem.store("Happy news!", emotion=ev)
        assert item.emotion is not None
        assert item.emotion.joy == 0.8

    def test_store_auto_emotion(self):
        from stellar_memory import StellarMemory, StellarConfig, EmotionConfig
        config = StellarConfig(
            db_path=":memory:",
            emotion=EmotionConfig(enabled=True),
        )
        mem = StellarMemory(config)
        item = mem.store("I am so happy and excited!!")
        assert item.emotion is not None
        assert item.emotion.joy > 0.0

    def test_store_no_emotion_when_disabled(self):
        from stellar_memory import StellarMemory, StellarConfig
        config = StellarConfig(db_path=":memory:")
        mem = StellarMemory(config)
        item = mem.store("I am happy")
        assert item.emotion is None

    def test_recall_emotion_filter(self):
        from stellar_memory import StellarMemory, StellarConfig
        config = StellarConfig(db_path=":memory:")
        mem = StellarMemory(config)
        # Store with explicit emotions
        mem.store("Happy day", emotion=EmotionVector(joy=0.9))
        mem.store("Sad news", emotion=EmotionVector(sadness=0.9))
        mem.store("Neutral info")  # no emotion

        results = mem.recall("day", emotion="joy")
        assert all(r.emotion and r.emotion.dominant == "joy" for r in results)


class TestEmotionDecay:
    """Test emotion-based decay adjustment."""

    def test_emotion_decay_boost(self):
        """Strong emotion -> slower decay (higher decay_days)."""
        from stellar_memory.config import DecayConfig, EmotionConfig
        from stellar_memory.decay_manager import DecayManager
        from stellar_memory.models import MemoryItem, EmotionVector

        decay_cfg = DecayConfig(enabled=True, decay_days=30)
        emotion_cfg = EmotionConfig(
            enabled=True,
            decay_boost_threshold=0.7,
            decay_boost_factor=0.5,
        )
        mgr = DecayManager(decay_cfg, emotion_config=emotion_cfg)

        item = MemoryItem.create("strong emotion memory")
        item.emotion = EmotionVector(joy=0.9)
        adjusted = mgr._adjusted_decay_days(item, 30)
        # 30 / 0.5 = 60 -> slower decay
        assert adjusted == 60

    def test_emotion_decay_penalty(self):
        """Weak emotion -> faster decay (lower decay_days)."""
        from stellar_memory.config import DecayConfig, EmotionConfig
        from stellar_memory.decay_manager import DecayManager
        from stellar_memory.models import MemoryItem, EmotionVector

        decay_cfg = DecayConfig(enabled=True, decay_days=30)
        emotion_cfg = EmotionConfig(
            enabled=True,
            decay_penalty_threshold=0.3,
            decay_penalty_factor=1.5,
        )
        mgr = DecayManager(decay_cfg, emotion_config=emotion_cfg)

        item = MemoryItem.create("weak emotion memory")
        item.emotion = EmotionVector(joy=0.1)
        adjusted = mgr._adjusted_decay_days(item, 30)
        # 30 * 1.5 = 45 -> faster decay
        assert adjusted == 45

    def test_no_emotion_no_adjustment(self):
        """No emotion -> no adjustment."""
        from stellar_memory.config import DecayConfig, EmotionConfig
        from stellar_memory.decay_manager import DecayManager
        from stellar_memory.models import MemoryItem

        decay_cfg = DecayConfig(enabled=True, decay_days=30)
        emotion_cfg = EmotionConfig(enabled=True)
        mgr = DecayManager(decay_cfg, emotion_config=emotion_cfg)

        item = MemoryItem.create("no emotion")
        adjusted = mgr._adjusted_decay_days(item, 30)
        assert adjusted == 30

    def test_emoji_emotion_detection(self):
        """Emoji patterns should be detected."""
        analyzer = EmotionAnalyzer(EmotionConfig(enabled=True))
        ev = analyzer.analyze("Great day \U0001F60A\U0001F389")
        assert ev.joy > 0.0
