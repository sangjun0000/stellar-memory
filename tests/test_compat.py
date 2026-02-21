"""Tests for v2 backward compatibility (v3.0 SDK)."""

import pytest
import warnings


class TestV3CoreExports:
    """v3.0 core exports should be available without warnings."""

    def test_stellar_memory_importable(self):
        from stellar_memory import StellarMemory
        assert StellarMemory is not None

    def test_builder_importable(self):
        from stellar_memory import StellarBuilder, Preset
        assert StellarBuilder is not None
        assert Preset is not None

    def test_models_importable(self):
        from stellar_memory import MemoryItem, MemoryStats
        assert MemoryItem is not None
        assert MemoryStats is not None

    def test_plugin_importable(self):
        from stellar_memory import MemoryPlugin
        assert MemoryPlugin is not None

    def test_protocols_importable(self):
        from stellar_memory import (
            StorageBackendProtocol, EmbedderProvider,
            ImportanceEvaluator, MemoryStore,
        )
        assert StorageBackendProtocol is not None
        assert EmbedderProvider is not None

    def test_config_importable(self):
        from stellar_memory import StellarConfig
        assert StellarConfig is not None

    def test_all_has_11_entries(self):
        import stellar_memory
        assert len(stellar_memory.__all__) == 11


class TestV2CompatWarnings:
    """v2.0 imports should work but produce DeprecationWarning."""

    def test_config_class_deprecated(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from stellar_memory import MemoryFunctionConfig  # noqa: F401
            # Should have at least one deprecation warning
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1
            assert "deprecated" in str(deprecation_warnings[0].message).lower()

    def test_event_bus_deprecated(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from stellar_memory import EventBus  # noqa: F401
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1

    def test_model_class_deprecated(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from stellar_memory import ScoreBreakdown  # noqa: F401
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1


class TestV2DirectImports:
    """v2.0 direct module imports should still work without warnings."""

    def test_config_direct_import(self):
        from stellar_memory.config import MemoryFunctionConfig
        assert MemoryFunctionConfig is not None

    def test_models_direct_import(self):
        from stellar_memory.models import ScoreBreakdown
        assert ScoreBreakdown is not None

    def test_event_bus_direct_import(self):
        from stellar_memory.event_bus import EventBus
        assert EventBus is not None


class TestCompatModule:
    """stellar_memory.compat provides all v2 exports."""

    def test_compat_config(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from stellar_memory.compat import MemoryFunctionConfig  # noqa: F401

    def test_compat_models(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from stellar_memory.compat import ScoreBreakdown  # noqa: F401

    def test_compat_unknown_raises(self):
        with pytest.raises((AttributeError, ImportError)):
            from stellar_memory.compat import NonExistentClass  # noqa: F401


class TestCelestialEngineDeprecation:
    """celestial_engine import should produce deprecation warning."""

    def test_celestial_engine_warns(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            import celestial_engine  # noqa: F401
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1
            assert "deprecated" in str(deprecation_warnings[0].message).lower()
