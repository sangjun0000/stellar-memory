"""Stellar Memory configuration classes."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ZoneConfig:
    zone_id: int
    name: str
    max_slots: int | None
    importance_min: float
    importance_max: float = float("inf")


DEFAULT_ZONES = [
    ZoneConfig(0, "core", max_slots=20, importance_min=0.8),
    ZoneConfig(1, "inner", max_slots=100, importance_min=0.5, importance_max=0.8),
    ZoneConfig(2, "outer", max_slots=1000, importance_min=0.2, importance_max=0.5),
    ZoneConfig(3, "belt", max_slots=None, importance_min=0.0, importance_max=0.2),
    ZoneConfig(4, "cloud", max_slots=None, importance_min=float("-inf"), importance_max=0.0),
]


@dataclass
class MemoryFunctionConfig:
    w_recall: float = 0.3
    w_freshness: float = 0.3
    w_arbitrary: float = 0.25
    w_context: float = 0.15
    w_emotion: float = 0.0  # P7: 0.0 by default (inactive), 0.15 when emotion enabled
    max_recall: int = 1000
    decay_alpha: float = 0.0001
    freshness_cap: float = -1.0


@dataclass
class EmbedderConfig:
    model_name: str = "all-MiniLM-L6-v2"
    dimension: int = 384
    batch_size: int = 32
    enabled: bool = True
    provider: str = "sentence-transformers"  # "sentence-transformers" | "openai" | "ollama"


@dataclass
class LLMConfig:
    provider: str = "anthropic"
    model: str = "claude-haiku-4-5-20251001"
    api_key_env: str = "ANTHROPIC_API_KEY"
    max_tokens: int = 256
    enabled: bool = True
    base_url: str | None = None  # for Ollama custom endpoint


@dataclass
class TunerConfig:
    enabled: bool = True
    min_feedback: int = 50
    max_delta: float = 0.05
    weight_min: float = 0.05
    weight_max: float = 0.5
    feedback_db_path: str = "stellar_feedback.db"


@dataclass
class ConsolidationConfig:
    enabled: bool = True
    similarity_threshold: float = 0.85
    on_store: bool = True
    on_reorbit: bool = False
    max_content_length: int = 2000


@dataclass
class SessionConfig:
    enabled: bool = True
    auto_summarize: bool = True
    summary_max_items: int = 5
    scope_current_first: bool = True


@dataclass
class NamespaceConfig:
    enabled: bool = True
    base_path: str = "stellar_data"


@dataclass
class GraphConfig:
    enabled: bool = True
    auto_link: bool = True
    auto_link_threshold: float = 0.7
    max_edges_per_item: int = 20
    persistent: bool = True


@dataclass
class GraphAnalyticsConfig:
    enabled: bool = True
    community_min_size: int = 2


@dataclass
class AdaptiveDecayConfig:
    enabled: bool = False
    importance_weight: float = 1.0
    decay_curve: str = "linear"  # "linear" | "exponential" | "sigmoid"
    zone_factor: bool = True


@dataclass
class DecayConfig:
    enabled: bool = True
    decay_days: int = 30
    auto_forget_days: int = 90
    min_zone_for_decay: int = 2
    adaptive: AdaptiveDecayConfig = field(default_factory=AdaptiveDecayConfig)


@dataclass
class EventLoggerConfig:
    enabled: bool = True
    log_path: str = "stellar_events.jsonl"
    max_size_mb: float = 10.0


@dataclass
class RecallConfig:
    graph_boost_enabled: bool = True
    graph_boost_score: float = 0.1
    graph_boost_depth: int = 1


@dataclass
class VectorIndexConfig:
    enabled: bool = True
    backend: str = "brute_force"  # "brute_force" | "ball_tree" | "faiss"
    rebuild_on_start: bool = True
    ball_tree_leaf_size: int = 40


@dataclass
class SummarizationConfig:
    enabled: bool = True
    min_length: int = 100
    max_summary_length: int = 200
    importance_boost: float = 0.1




# P6 Config classes

@dataclass
class StorageConfig:
    backend: str = "sqlite"  # "sqlite" | "postgresql" | "memory"
    db_url: str | None = None
    pool_size: int = 10
    redis_url: str | None = None
    redis_ttl: int = 300
    redis_cached_zones: tuple = (0, 1)


@dataclass
class SyncConfig:
    enabled: bool = False
    agent_id: str = ""
    ws_host: str = "0.0.0.0"
    ws_port: int = 8765
    remote_url: str | None = None
    auto_start_server: bool = False


@dataclass
class SecurityConfig:
    enabled: bool = False
    encryption_key_env: str = "STELLAR_ENCRYPTION_KEY"
    access_control: bool = False
    default_role: str = "writer"
    roles: dict | None = None
    audit_enabled: bool = True
    auto_encrypt_tags: list[str] = field(
        default_factory=lambda: ["secret", "sensitive", "api_key"]
    )


@dataclass
class ConnectorConfig:
    enabled: bool = False
    web_enabled: bool = True
    file_enabled: bool = True
    api_enabled: bool = True
    auto_summarize: bool = True
    dedup_check: bool = True


@dataclass
class DashboardConfig:
    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 8080
    auto_start: bool = False


# P7 Config classes

@dataclass
class EmotionConfig:
    enabled: bool = False  # default off for backward compat
    use_llm: bool = False
    decay_boost_threshold: float = 0.7
    decay_boost_factor: float = 0.5
    decay_penalty_threshold: float = 0.3
    decay_penalty_factor: float = 1.5


@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 9000
    api_key_env: str = "STELLAR_API_KEY"
    rate_limit: int = 60
    cors_origins: list[str] = field(default_factory=lambda: ["*"])


# P9 Config classes

@dataclass
class MetacognitionConfig:
    enabled: bool = False
    confidence_alpha: float = 0.4
    confidence_beta: float = 0.3
    confidence_gamma: float = 0.3
    low_confidence_threshold: float = 0.3
    use_llm_for_gaps: bool = False


@dataclass
class SelfLearningConfig:
    enabled: bool = False
    learning_rate: float = 0.03
    min_logs: int = 50
    max_delta: float = 0.1
    auto_optimize: bool = False
    auto_optimize_interval: int = 1000


@dataclass
class MultimodalConfig:
    enabled: bool = False
    code_language_detect: bool = True
    json_schema_extract: bool = True


@dataclass
class ReasoningConfig:
    enabled: bool = False
    max_sources: int = 10
    use_llm: bool = True
    contradiction_check: bool = True


@dataclass
class BenchmarkConfig:
    default_queries: int = 100
    default_dataset: str = "standard"
    default_seed: int = 42
    output_format: str = "json"


# Internal configs (not part of public SDK API)

@dataclass
class KnowledgeBaseConfig:
    enabled: bool = True
    auto_detect_project: bool = True
    auto_import_ai_configs: bool = False
    preference_importance: float = 0.95
    rule_importance: float = 0.9
    context_importance: float = 0.85


@dataclass
class StellarConfig:
    memory_function: MemoryFunctionConfig = field(default_factory=MemoryFunctionConfig)
    zones: list[ZoneConfig] = field(default_factory=lambda: list(DEFAULT_ZONES))
    reorbit_interval: int = 300
    db_path: str = "stellar_memory.db"
    log_level: str = "INFO"
    auto_start_scheduler: bool = True
    embedder: EmbedderConfig = field(default_factory=EmbedderConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    tuner: TunerConfig = field(default_factory=TunerConfig)
    consolidation: ConsolidationConfig = field(default_factory=ConsolidationConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    namespace: NamespaceConfig = field(default_factory=NamespaceConfig)
    graph: GraphConfig = field(default_factory=GraphConfig)
    decay: DecayConfig = field(default_factory=DecayConfig)
    event_logger: EventLoggerConfig = field(default_factory=EventLoggerConfig)
    recall_boost: RecallConfig = field(default_factory=RecallConfig)
    vector_index: VectorIndexConfig = field(default_factory=VectorIndexConfig)
    summarization: SummarizationConfig = field(default_factory=SummarizationConfig)
    graph_analytics: GraphAnalyticsConfig = field(default_factory=GraphAnalyticsConfig)
    # P6 fields
    storage: StorageConfig = field(default_factory=StorageConfig)
    sync: SyncConfig = field(default_factory=SyncConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    connectors: ConnectorConfig = field(default_factory=ConnectorConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    # P7 fields
    emotion: EmotionConfig = field(default_factory=EmotionConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    # P9 fields
    metacognition: MetacognitionConfig = field(default_factory=MetacognitionConfig)
    self_learning: SelfLearningConfig = field(default_factory=SelfLearningConfig)
    multimodal: MultimodalConfig = field(default_factory=MultimodalConfig)
    reasoning: ReasoningConfig = field(default_factory=ReasoningConfig)
    benchmark: BenchmarkConfig = field(default_factory=BenchmarkConfig)
    # Internal (not part of public SDK API)
    knowledge_base: KnowledgeBaseConfig = field(default_factory=KnowledgeBaseConfig)

    @classmethod
    def from_json(cls, path: str | Path) -> StellarConfig:
        """Load configuration from a JSON file."""
        with open(path) as f:
            data = json.load(f)
        mf_data = data.get("memory_function", {})
        mf = MemoryFunctionConfig(**mf_data)
        zones = []
        for z in data.get("zones", []):
            imp_max = z.get("importance_max", float("inf"))
            zones.append(ZoneConfig(
                zone_id=z["zone_id"], name=z["name"],
                max_slots=z.get("max_slots"),
                importance_min=z["importance_min"],
                importance_max=imp_max,
            ))
        return cls(
            memory_function=mf,
            zones=zones or list(DEFAULT_ZONES),
            reorbit_interval=data.get("reorbit_interval", 300),
            db_path=data.get("db_path", "stellar_memory.db"),
        )
