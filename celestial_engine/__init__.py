"""Celestial Memory Engine - DEPRECATED in v3.0.

Use stellar_memory instead::

    # Before:
    from celestial_engine import CelestialMemory
    memory = CelestialMemory()

    # After:
    from stellar_memory import StellarBuilder, Preset
    memory = StellarBuilder(Preset.MINIMAL).with_sqlite("celestial_memory.db").build()

See migration guide: docs/migration-v2-to-v3.md
"""

from __future__ import annotations

import warnings

warnings.warn(
    "celestial_engine is deprecated in v3.0. Use stellar_memory instead. "
    "See docs/migration-v2-to-v3.md for migration guide.",
    DeprecationWarning,
    stacklevel=2,
)

# Thin shim: re-export stellar_memory classes under old names
from stellar_memory import StellarMemory as CelestialMemory  # noqa: F401
from stellar_memory import StellarBuilder  # noqa: F401
from stellar_memory import Preset  # noqa: F401
from stellar_memory import StellarConfig  # noqa: F401
from stellar_memory import MemoryItem as CelestialItem  # noqa: F401
from stellar_memory import MemoryStats  # noqa: F401
from stellar_memory.models import ScoreBreakdown, ReorbitResult  # noqa: F401
from stellar_memory.config import (  # noqa: F401
    MemoryFunctionConfig,
    ZoneConfig,
    DEFAULT_ZONES,
)

# Legacy evaluator imports
from stellar_memory.protocols import ImportanceEvaluator  # noqa: F401
from stellar_memory.importance_evaluator import (  # noqa: F401
    RuleBasedEvaluator,
    LLMEvaluator,
    NullEvaluator as DefaultEvaluator,
)

__version__ = "3.0.0-deprecated"

__all__ = [
    "CelestialMemory",
    "CelestialItem",
    "StellarBuilder",
    "Preset",
    "StellarConfig",
    "MemoryStats",
    "MemoryFunctionConfig",
    "ZoneConfig",
    "ScoreBreakdown",
    "ReorbitResult",
    "DEFAULT_ZONES",
    "ImportanceEvaluator",
    "DefaultEvaluator",
    "RuleBasedEvaluator",
    "LLMEvaluator",
]
