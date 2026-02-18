"""Tests for P7 stream module: MemoryStream, timeline, narrate."""

import time
import pytest

from stellar_memory import StellarMemory, StellarConfig
from stellar_memory.models import TimelineEntry, EmotionVector
from stellar_memory.stream import MemoryStream


class TestMemoryStream:
    def _make_memory(self):
        config = StellarConfig(db_path=":memory:")
        return StellarMemory(config)

    def test_timeline_empty(self):
        mem = self._make_memory()
        entries = mem.timeline()
        assert entries == []

    def test_timeline_returns_entries(self):
        mem = self._make_memory()
        mem.store("First memory")
        mem.store("Second memory")
        entries = mem.timeline()
        assert len(entries) == 2
        assert isinstance(entries[0], TimelineEntry)

    def test_timeline_sorted(self):
        mem = self._make_memory()
        mem.store("A")
        time.sleep(0.01)
        mem.store("B")
        entries = mem.timeline()
        assert entries[0].timestamp <= entries[1].timestamp

    def test_timeline_limit(self):
        mem = self._make_memory()
        for i in range(10):
            mem.store(f"Memory {i}")
        entries = mem.timeline(limit=3)
        assert len(entries) == 3

    def test_timeline_time_range(self):
        mem = self._make_memory()
        t1 = time.time()
        mem.store("Before")
        time.sleep(0.01)
        mid = time.time()
        time.sleep(0.01)
        mem.store("After")
        t2 = time.time()
        # Only items after mid
        entries = mem.timeline(start=mid, end=t2)
        assert len(entries) == 1
        assert "After" in entries[0].content

    def test_timeline_with_emotion(self):
        mem = self._make_memory()
        ev = EmotionVector(joy=0.8)
        mem.store("Happy!", emotion=ev)
        entries = mem.timeline()
        assert entries[0].emotion is not None
        assert entries[0].emotion.joy == 0.8

    def test_narrate_empty(self):
        mem = self._make_memory()
        result = mem.narrate("anything")
        assert result == ""

    def test_narrate_without_llm(self):
        mem = self._make_memory()
        mem.store("Python is great for AI")
        mem.store("Machine learning uses Python")
        result = mem.narrate("Python", limit=5)
        assert len(result) > 0

    def test_stellar_timeline_method(self):
        mem = self._make_memory()
        mem.store("Hello")
        entries = mem.timeline()
        assert len(entries) == 1

    def test_stream_property(self):
        mem = self._make_memory()
        assert isinstance(mem.stream, MemoryStream)
        # Same instance on second access
        assert mem.stream is mem.stream


class TestParseTime:
    def test_float(self):
        assert MemoryStream._parse_time(123.0) == 123.0

    def test_int(self):
        assert MemoryStream._parse_time(100) == 100.0

    def test_date_string(self):
        ts = MemoryStream._parse_time("2026-02-17")
        assert ts > 0

    def test_datetime_string(self):
        ts = MemoryStream._parse_time("2026-02-17 14:30")
        assert ts > 0

    def test_invalid_string(self):
        with pytest.raises(ValueError, match="Cannot parse"):
            MemoryStream._parse_time("not-a-date")

    def test_invalid_type(self):
        with pytest.raises(TypeError):
            MemoryStream._parse_time([1, 2, 3])
