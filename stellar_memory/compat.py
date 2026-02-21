"""Backward compatibility for v2.0 imports.

Usage::

    # If you used v2.0 imports like:
    from stellar_memory import EventBus, MemoryGraph, ...

    # You can temporarily use:
    from stellar_memory.compat import EventBus, MemoryGraph, ...

    # But prefer updating to direct module imports:
    from stellar_memory.event_bus import EventBus
    from stellar_memory.memory_graph import MemoryGraph
"""

from __future__ import annotations

import importlib
import warnings

# Map of v2 export names to (module_path, attribute_name)
_V2_MAP: dict[str, tuple[str, str]] = {
    # Config classes
    "MemoryFunctionConfig": (".config", "MemoryFunctionConfig"),
    "ZoneConfig": (".config", "ZoneConfig"),
    "EmbedderConfig": (".config", "EmbedderConfig"),
    "LLMConfig": (".config", "LLMConfig"),
    "TunerConfig": (".config", "TunerConfig"),
    "ConsolidationConfig": (".config", "ConsolidationConfig"),
    "SessionConfig": (".config", "SessionConfig"),
    "NamespaceConfig": (".config", "NamespaceConfig"),
    "GraphConfig": (".config", "GraphConfig"),
    "DecayConfig": (".config", "DecayConfig"),
    "EventLoggerConfig": (".config", "EventLoggerConfig"),
    "RecallConfig": (".config", "RecallConfig"),
    "VectorIndexConfig": (".config", "VectorIndexConfig"),
    "SummarizationConfig": (".config", "SummarizationConfig"),
    "AdaptiveDecayConfig": (".config", "AdaptiveDecayConfig"),
    "GraphAnalyticsConfig": (".config", "GraphAnalyticsConfig"),
    "StorageConfig": (".config", "StorageConfig"),
    "SyncConfig": (".config", "SyncConfig"),
    "SecurityConfig": (".config", "SecurityConfig"),
    "ConnectorConfig": (".config", "ConnectorConfig"),
    "DashboardConfig": (".config", "DashboardConfig"),
    "EmotionConfig": (".config", "EmotionConfig"),
    "ServerConfig": (".config", "ServerConfig"),
    "MetacognitionConfig": (".config", "MetacognitionConfig"),
    "SelfLearningConfig": (".config", "SelfLearningConfig"),
    "MultimodalConfig": (".config", "MultimodalConfig"),
    "ReasoningConfig": (".config", "ReasoningConfig"),
    "BenchmarkConfig": (".config", "BenchmarkConfig"),
    # Models
    "ScoreBreakdown": (".models", "ScoreBreakdown"),
    "ReorbitResult": (".models", "ReorbitResult"),
    "EvaluationResult": (".models", "EvaluationResult"),
    "FeedbackRecord": (".models", "FeedbackRecord"),
    "ConsolidationResult": (".models", "ConsolidationResult"),
    "SessionInfo": (".models", "SessionInfo"),
    "MemorySnapshot": (".models", "MemorySnapshot"),
    "MemoryEdge": (".models", "MemoryEdge"),
    "DecayResult": (".models", "DecayResult"),
    "HealthStatus": (".models", "HealthStatus"),
    "SummarizationResult": (".models", "SummarizationResult"),
    "ChangeEvent": (".models", "ChangeEvent"),
    "AccessRole": (".models", "AccessRole"),
    "IngestResult": (".models", "IngestResult"),
    "ZoneDistribution": (".models", "ZoneDistribution"),
    "EmotionVector": (".models", "EmotionVector"),
    "TimelineEntry": (".models", "TimelineEntry"),
    "IntrospectionResult": (".models", "IntrospectionResult"),
    "ConfidentRecall": (".models", "ConfidentRecall"),
    "RecallLog": (".models", "RecallLog"),
    "OptimizationReport": (".models", "OptimizationReport"),
    "ReasoningResult": (".models", "ReasoningResult"),
    "Contradiction": (".models", "Contradiction"),
    "BenchmarkReport": (".models", "BenchmarkReport"),
    # Core classes
    "EventBus": (".event_bus", "EventBus"),
    "MemoryGraph": (".memory_graph", "MemoryGraph"),
    "PersistentMemoryGraph": (".persistent_graph", "PersistentMemoryGraph"),
    "NamespaceManager": (".namespace", "NamespaceManager"),
    "DecayManager": (".decay_manager", "DecayManager"),
    "EventLogger": (".event_logger", "EventLogger"),
    "MemoryMiddleware": (".llm_adapter", "MemoryMiddleware"),
    "AnthropicAdapter": (".llm_adapter", "AnthropicAdapter"),
    "VectorIndex": (".vector_index", "VectorIndex"),
    "BruteForceIndex": (".vector_index", "BruteForceIndex"),
    "BallTreeIndex": (".vector_index", "BallTreeIndex"),
    "MemorySummarizer": (".summarizer", "MemorySummarizer"),
    "AdaptiveDecayManager": (".adaptive_decay", "AdaptiveDecayManager"),
    "GraphAnalyzer": (".graph_analyzer", "GraphAnalyzer"),
    "GraphStats": (".graph_analyzer", "GraphStats"),
    "CentralityResult": (".graph_analyzer", "CentralityResult"),
    "ProviderRegistry": (".providers", "ProviderRegistry"),
    "StorageBackend": (".storage", "StorageBackend"),
    "EncryptionManager": (".security.encryption", "EncryptionManager"),
    "AccessControl": (".security.access_control", "AccessControl"),
    "SecurityAudit": (".security.audit", "SecurityAudit"),
    "MemorySyncManager": (".sync", "MemorySyncManager"),
    "EmotionAnalyzer": (".emotion", "EmotionAnalyzer"),
    "MemoryStream": (".stream", "MemoryStream"),
    "Introspector": (".metacognition", "Introspector"),
    "ConfidenceScorer": (".metacognition", "ConfidenceScorer"),
    "ContentTypeHandler": (".multimodal", "ContentTypeHandler"),
    "TextHandler": (".multimodal", "TextHandler"),
    "CodeHandler": (".multimodal", "CodeHandler"),
    "JsonHandler": (".multimodal", "JsonHandler"),
    "get_handler": (".multimodal", "get_handler"),
    "detect_content_type": (".multimodal", "detect_content_type"),
    "PatternCollector": (".self_learning", "PatternCollector"),
    "WeightOptimizer": (".self_learning", "WeightOptimizer"),
    "MemoryReasoner": (".reasoning", "MemoryReasoner"),
    "ContradictionDetector": (".reasoning", "ContradictionDetector"),
    "StandardDataset": (".benchmark", "StandardDataset"),
    "MemoryBenchmark": (".benchmark", "MemoryBenchmark"),
}


def __getattr__(name: str):
    if name in _V2_MAP:
        module_path, attr = _V2_MAP[name]
        warnings.warn(
            f"Importing {name} from stellar_memory.compat is deprecated. "
            f"Use 'from stellar_memory{module_path} import {attr}' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        module = importlib.import_module(module_path, package="stellar_memory")
        return getattr(module, attr)
    raise AttributeError(f"module 'stellar_memory.compat' has no attribute {name}")
