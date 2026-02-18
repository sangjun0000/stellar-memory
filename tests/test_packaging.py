"""Tests for P7 packaging: imports, version, public API."""

import pytest


class TestPackaging:
    def test_import_stellar_memory(self):
        import stellar_memory
        assert stellar_memory is not None

    def test_version(self):
        import stellar_memory
        assert stellar_memory.__version__ is not None
        assert len(stellar_memory.__version__) > 0

    def test_quick_start_3lines(self):
        from stellar_memory import StellarMemory
        memory = StellarMemory()
        memory.store("User prefers Python")
        results = memory.recall("programming preference")
        assert isinstance(results, list)

    def test_public_api_exports(self):
        import stellar_memory
        assert "StellarMemory" in stellar_memory.__all__
        assert "StellarConfig" in stellar_memory.__all__
        assert "MemoryItem" in stellar_memory.__all__
        assert "EmotionVector" in stellar_memory.__all__
        assert "TimelineEntry" in stellar_memory.__all__
        assert "EmotionConfig" in stellar_memory.__all__
        assert "ServerConfig" in stellar_memory.__all__
        assert "EmotionAnalyzer" in stellar_memory.__all__
        assert "MemoryStream" in stellar_memory.__all__

    def test_emotion_vector_importable(self):
        from stellar_memory import EmotionVector
        ev = EmotionVector(joy=0.5)
        assert ev.joy == 0.5

    def test_timeline_entry_importable(self):
        from stellar_memory import TimelineEntry
        te = TimelineEntry(timestamp=1.0, memory_id="x", content="hi")
        assert te.content == "hi"

    def test_optional_import_no_crash(self):
        """Core works without optional deps."""
        from stellar_memory import StellarMemory, StellarConfig
        config = StellarConfig(db_path=":memory:")
        mem = StellarMemory(config)
        item = mem.store("test")
        assert item.id

    def test_cli_entrypoint(self):
        from stellar_memory.cli import main
        assert callable(main)
