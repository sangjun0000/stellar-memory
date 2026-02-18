"""Stellar Memory - A celestial-structure-based AI memory management system.

Give any AI human-like memory, built on a celestial structure.
"""

from stellar_memory.stellar import StellarMemory
from stellar_memory.config import (
    StellarConfig, MemoryFunctionConfig, ZoneConfig,
    EmbedderConfig, LLMConfig, TunerConfig,
    ConsolidationConfig, SessionConfig,
    EventConfig, NamespaceConfig, GraphConfig,
    DecayConfig, EventLoggerConfig, RecallConfig,
    VectorIndexConfig, SummarizationConfig,
    AdaptiveDecayConfig, GraphAnalyticsConfig,
    StorageConfig, SyncConfig, SecurityConfig,
    ConnectorConfig, DashboardConfig,
    EmotionConfig, ServerConfig,
    MetacognitionConfig, SelfLearningConfig,
    MultimodalConfig, ReasoningConfig, BenchmarkConfig,
)
from stellar_memory.models import (
    MemoryItem, ScoreBreakdown, ReorbitResult, MemoryStats,
    EvaluationResult, FeedbackRecord,
    ConsolidationResult, SessionInfo, MemorySnapshot,
    MemoryEdge, DecayResult, HealthStatus, SummarizationResult,
    ChangeEvent, AccessRole, IngestResult, ZoneDistribution,
    EmotionVector, TimelineEntry,
    IntrospectionResult, ConfidentRecall, RecallLog,
    OptimizationReport, ReasoningResult, Contradiction,
    BenchmarkReport,
)
from stellar_memory.event_bus import EventBus
from stellar_memory.memory_graph import MemoryGraph
from stellar_memory.persistent_graph import PersistentMemoryGraph
from stellar_memory.namespace import NamespaceManager
from stellar_memory.decay_manager import DecayManager
from stellar_memory.event_logger import EventLogger
from stellar_memory.llm_adapter import MemoryMiddleware, AnthropicAdapter
from stellar_memory.vector_index import VectorIndex, BruteForceIndex, BallTreeIndex
from stellar_memory.summarizer import MemorySummarizer
from stellar_memory.adaptive_decay import AdaptiveDecayManager
from stellar_memory.graph_analyzer import GraphAnalyzer, GraphStats, CentralityResult
from stellar_memory.providers import ProviderRegistry
from stellar_memory.storage import StorageBackend
from stellar_memory.security.encryption import EncryptionManager
from stellar_memory.security.access_control import AccessControl
from stellar_memory.security.audit import SecurityAudit
from stellar_memory.sync import MemorySyncManager
from stellar_memory.emotion import EmotionAnalyzer
from stellar_memory.stream import MemoryStream
from stellar_memory.metacognition import Introspector, ConfidenceScorer
from stellar_memory.multimodal import (
    ContentTypeHandler, TextHandler, CodeHandler, JsonHandler,
    get_handler, detect_content_type,
)
from stellar_memory.self_learning import PatternCollector, WeightOptimizer
from stellar_memory.reasoning import MemoryReasoner, ContradictionDetector
from stellar_memory.benchmark import StandardDataset, MemoryBenchmark

try:
    from importlib.metadata import version as _pkg_version
    __version__ = _pkg_version("stellar-memory")
except Exception:
    __version__ = "1.0.0"

__all__ = [
    "StellarMemory",
    "StellarConfig",
    "MemoryFunctionConfig",
    "ZoneConfig",
    "EmbedderConfig",
    "LLMConfig",
    "TunerConfig",
    "ConsolidationConfig",
    "SessionConfig",
    "EventConfig",
    "NamespaceConfig",
    "GraphConfig",
    "DecayConfig",
    "EventLoggerConfig",
    "RecallConfig",
    "VectorIndexConfig",
    "SummarizationConfig",
    "AdaptiveDecayConfig",
    "GraphAnalyticsConfig",
    "MemoryItem",
    "ScoreBreakdown",
    "ReorbitResult",
    "MemoryStats",
    "EvaluationResult",
    "FeedbackRecord",
    "ConsolidationResult",
    "SessionInfo",
    "MemorySnapshot",
    "MemoryEdge",
    "DecayResult",
    "HealthStatus",
    "SummarizationResult",
    "EventBus",
    "MemoryGraph",
    "PersistentMemoryGraph",
    "NamespaceManager",
    "DecayManager",
    "EventLogger",
    "MemoryMiddleware",
    "AnthropicAdapter",
    "VectorIndex",
    "BruteForceIndex",
    "BallTreeIndex",
    "MemorySummarizer",
    "AdaptiveDecayManager",
    "GraphAnalyzer",
    "GraphStats",
    "CentralityResult",
    "ProviderRegistry",
    "StorageConfig",
    "SyncConfig",
    "SecurityConfig",
    "ConnectorConfig",
    "DashboardConfig",
    "ChangeEvent",
    "AccessRole",
    "IngestResult",
    "ZoneDistribution",
    "StorageBackend",
    "EncryptionManager",
    "AccessControl",
    "SecurityAudit",
    "MemorySyncManager",
    # P7
    "EmotionConfig",
    "ServerConfig",
    "EmotionVector",
    "TimelineEntry",
    "EmotionAnalyzer",
    "MemoryStream",
    # P9
    "MetacognitionConfig",
    "SelfLearningConfig",
    "MultimodalConfig",
    "ReasoningConfig",
    "BenchmarkConfig",
    "IntrospectionResult",
    "ConfidentRecall",
    "RecallLog",
    "OptimizationReport",
    "ReasoningResult",
    "Contradiction",
    "BenchmarkReport",
    "Introspector",
    "ConfidenceScorer",
    "ContentTypeHandler",
    "TextHandler",
    "CodeHandler",
    "JsonHandler",
    "get_handler",
    "detect_content_type",
    "PatternCollector",
    "WeightOptimizer",
    "MemoryReasoner",
    "ContradictionDetector",
    "StandardDataset",
    "MemoryBenchmark",
]
