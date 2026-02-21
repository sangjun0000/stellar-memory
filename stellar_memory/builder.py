"""StellarBuilder - Fluent builder for StellarMemory instances.

Provides preset-based and custom configuration for easy initialization.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from stellar_memory.config import (
    StellarConfig,
    MemoryFunctionConfig,
    ZoneConfig,
    EmbedderConfig,
    LLMConfig,
    TunerConfig,
    ConsolidationConfig,
    SessionConfig,
    GraphConfig,
    DecayConfig,
    EmotionConfig,
    MetacognitionConfig,
    SelfLearningConfig,
    ReasoningConfig,
    StorageConfig,
    VectorIndexConfig,
    SummarizationConfig,
    BenchmarkConfig,
    DEFAULT_ZONES,
)

if TYPE_CHECKING:
    from stellar_memory.protocols import EmbedderProvider, ImportanceEvaluator, StorageBackendProtocol
    from stellar_memory.plugin import MemoryPlugin
    from stellar_memory.stellar import StellarMemory


class Preset(Enum):
    """Pre-configured memory profiles."""

    MINIMAL = "minimal"
    CHAT = "chat"
    AGENT = "agent"
    KNOWLEDGE = "knowledge"
    RESEARCH = "research"


# Zone definitions for minimal preset (3 zones)
_MINIMAL_ZONES = [
    ZoneConfig(0, "core", max_slots=20, importance_min=0.8),
    ZoneConfig(1, "active", max_slots=50, importance_min=0.4, importance_max=0.8),
    ZoneConfig(2, "archive", max_slots=200, importance_min=0.0, importance_max=0.4),
]


class StellarBuilder:
    """Fluent builder for StellarMemory instances.

    Examples::

        # Minimal (3 lines)
        memory = StellarBuilder().build()

        # Preset
        memory = StellarBuilder(Preset.AGENT).with_sqlite("brain.db").build()

        # Custom
        memory = (
            StellarBuilder()
            .with_sqlite("./memory.db")
            .with_embeddings()
            .with_emotions()
            .with_graph()
            .build()
        )
    """

    def __init__(self, preset: Preset = Preset.MINIMAL):
        self._preset = preset
        self._config = self._preset_to_config(preset)
        self._plugins: list[MemoryPlugin] = []
        self._storage_override: StorageBackendProtocol | None = None
        self._embedder_override: EmbedderProvider | None = None
        self._evaluator_override: ImportanceEvaluator | None = None
        self._namespace: str | None = None

    # === Storage ===

    def with_sqlite(self, path: str) -> StellarBuilder:
        """Use SQLite storage at the given path."""
        self._config.db_path = path
        return self

    def with_memory(self) -> StellarBuilder:
        """Use in-memory storage (no persistence)."""
        self._config.db_path = ":memory:"
        return self

    def with_postgres(self, db_url: str) -> StellarBuilder:
        """Use PostgreSQL storage."""
        self._config.storage = StorageConfig(backend="postgresql", db_url=db_url)
        return self

    def with_storage(self, backend: StorageBackendProtocol) -> StellarBuilder:
        """Use a custom storage backend."""
        self._storage_override = backend
        return self

    # === AI Features ===

    def with_embeddings(self, provider: str = "sentence-transformers",
                        model: str | None = None,
                        dimension: int = 384) -> StellarBuilder:
        """Enable semantic search with embeddings."""
        self._config.embedder = EmbedderConfig(
            enabled=True,
            provider=provider,
            model_name=model or "all-MiniLM-L6-v2",
            dimension=dimension,
        )
        return self

    def with_embedder(self, embedder: EmbedderProvider) -> StellarBuilder:
        """Use a custom embedder implementation."""
        self._embedder_override = embedder
        return self

    def with_llm(self, provider: str = "anthropic",
                 model: str | None = None,
                 api_key_env: str | None = None) -> StellarBuilder:
        """Enable LLM features (importance evaluation, reasoning)."""
        self._config.llm = LLMConfig(
            enabled=True,
            provider=provider,
            model=model or "claude-haiku-4-5-20251001",
            api_key_env=api_key_env or "ANTHROPIC_API_KEY",
        )
        return self

    # === Intelligence Features ===

    def with_emotions(self, use_llm: bool = False) -> StellarBuilder:
        """Enable emotion analysis."""
        self._config.emotion = EmotionConfig(enabled=True, use_llm=use_llm)
        return self

    def with_graph(self, auto_link: bool = True,
                   threshold: float = 0.7) -> StellarBuilder:
        """Enable memory graph connections."""
        self._config.graph = GraphConfig(
            enabled=True, auto_link=auto_link,
            auto_link_threshold=threshold,
        )
        return self

    def with_reasoning(self, use_llm: bool = True) -> StellarBuilder:
        """Enable reasoning engine."""
        self._config.reasoning = ReasoningConfig(enabled=True, use_llm=use_llm)
        return self

    def with_metacognition(self) -> StellarBuilder:
        """Enable metacognition (introspection, confidence scoring)."""
        self._config.metacognition = MetacognitionConfig(enabled=True)
        return self

    def with_self_learning(self, learning_rate: float = 0.03) -> StellarBuilder:
        """Enable self-learning (pattern collection, weight optimization)."""
        self._config.self_learning = SelfLearningConfig(
            enabled=True, learning_rate=learning_rate,
        )
        return self

    def with_sessions(self, auto_summarize: bool = True) -> StellarBuilder:
        """Enable session management."""
        self._config.session = SessionConfig(
            enabled=True, auto_summarize=auto_summarize,
        )
        return self

    # === Configuration ===

    def with_decay(self, rate: float = 0.0001,
                   decay_days: int = 30,
                   auto_forget_days: int = 90) -> StellarBuilder:
        """Configure decay parameters."""
        self._config.memory_function.decay_alpha = rate
        self._config.decay = DecayConfig(
            enabled=True,
            decay_days=decay_days,
            auto_forget_days=auto_forget_days,
        )
        return self

    def with_zones(self, core: int = 20, inner: int = 100,
                   outer: int = 1000, belt: int | None = None,
                   cloud: int | None = None) -> StellarBuilder:
        """Configure zone capacities."""
        capacities = [core, inner, outer, belt, cloud]
        for i, zone in enumerate(self._config.zones):
            if i < len(capacities) and capacities[i] is not None:
                zone.max_slots = capacities[i]
        return self

    def with_namespace(self, namespace: str) -> StellarBuilder:
        """Set namespace for memory isolation."""
        self._namespace = namespace
        return self

    def with_consolidation(self, threshold: float = 0.85) -> StellarBuilder:
        """Enable memory consolidation (deduplication)."""
        self._config.consolidation = ConsolidationConfig(
            enabled=True, similarity_threshold=threshold,
        )
        return self

    def with_summarization(self, min_length: int = 100) -> StellarBuilder:
        """Enable automatic summarization of long memories."""
        self._config.summarization = SummarizationConfig(
            enabled=True, min_length=min_length,
        )
        return self

    # === Plugin ===

    def with_plugin(self, plugin: MemoryPlugin) -> StellarBuilder:
        """Register a plugin."""
        self._plugins.append(plugin)
        return self

    # === Config Sources ===

    @classmethod
    def from_dict(cls, data: dict) -> StellarBuilder:
        """Create builder from a dictionary configuration."""
        preset_name = data.pop("preset", "minimal")
        try:
            preset = Preset(preset_name)
        except ValueError:
            preset = Preset.MINIMAL
        builder = cls(preset)

        # Apply storage
        if "db_path" in data:
            builder.with_sqlite(data.pop("db_path"))
        if "namespace" in data:
            builder.with_namespace(data.pop("namespace"))

        # Apply feature flags
        if data.get("embeddings"):
            emb = data.pop("embeddings")
            if isinstance(emb, dict):
                builder.with_embeddings(**emb)
            else:
                builder.with_embeddings()
        if data.get("emotions"):
            builder.with_emotions()
        if data.get("graph"):
            g = data.pop("graph")
            if isinstance(g, dict):
                builder.with_graph(**g)
            else:
                builder.with_graph()
        if data.get("reasoning"):
            builder.with_reasoning()
        if data.get("metacognition"):
            builder.with_metacognition()
        if data.get("self_learning"):
            builder.with_self_learning()

        return builder

    @classmethod
    def from_toml(cls, path: str) -> StellarBuilder:
        """Create builder from a TOML file."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]

        with open(path, "rb") as f:
            data = tomllib.load(f)

        section = data.get("stellar-memory", data)
        return cls.from_dict(dict(section))

    # === Build ===

    def build(self) -> StellarMemory:
        """Build and return a configured StellarMemory instance."""
        from stellar_memory.stellar import StellarMemory

        memory = StellarMemory(
            config=self._config,
            namespace=self._namespace,
        )

        # Apply overrides
        if self._embedder_override is not None:
            memory._embedder = self._embedder_override
        if self._evaluator_override is not None:
            memory._evaluator = self._evaluator_override

        # Register plugins
        for plugin in self._plugins:
            memory.use(plugin)

        return memory

    # === Internal ===

    def _preset_to_config(self, preset: Preset) -> StellarConfig:
        """Convert preset to StellarConfig."""
        configs = {
            Preset.MINIMAL: self._minimal_config,
            Preset.CHAT: self._chat_config,
            Preset.AGENT: self._agent_config,
            Preset.KNOWLEDGE: self._knowledge_config,
            Preset.RESEARCH: self._research_config,
        }
        return configs[preset]()

    def _minimal_config(self) -> StellarConfig:
        """3-zone, store/recall only."""
        return StellarConfig(
            zones=list(_MINIMAL_ZONES),
            embedder=EmbedderConfig(enabled=False),
            llm=LLMConfig(enabled=False),
            tuner=TunerConfig(enabled=False),
            consolidation=ConsolidationConfig(enabled=False),
            session=SessionConfig(enabled=False),
            graph=GraphConfig(enabled=False),
            decay=DecayConfig(enabled=False),
            summarization=SummarizationConfig(enabled=False),
            emotion=EmotionConfig(enabled=False),
            metacognition=MetacognitionConfig(enabled=False),
            self_learning=SelfLearningConfig(enabled=False),
            reasoning=ReasoningConfig(enabled=False),
        )

    def _chat_config(self) -> StellarConfig:
        """5-zone, session + emotion."""
        return StellarConfig(
            embedder=EmbedderConfig(enabled=False),
            llm=LLMConfig(enabled=False),
            tuner=TunerConfig(enabled=False),
            session=SessionConfig(enabled=True),
            emotion=EmotionConfig(enabled=True),
            graph=GraphConfig(enabled=False),
            reasoning=ReasoningConfig(enabled=False),
            metacognition=MetacognitionConfig(enabled=False),
            self_learning=SelfLearningConfig(enabled=False),
        )

    def _agent_config(self) -> StellarConfig:
        """5-zone, full intelligence suite for autonomous agents."""
        return StellarConfig(
            session=SessionConfig(enabled=True),
            emotion=EmotionConfig(enabled=True),
            graph=GraphConfig(enabled=True, auto_link=True),
            reasoning=ReasoningConfig(enabled=True),
            metacognition=MetacognitionConfig(enabled=True),
            self_learning=SelfLearningConfig(enabled=True),
        )

    def _knowledge_config(self) -> StellarConfig:
        """5-zone, graph + consolidation + summarization."""
        return StellarConfig(
            embedder=EmbedderConfig(enabled=False),
            llm=LLMConfig(enabled=False),
            tuner=TunerConfig(enabled=False),
            graph=GraphConfig(enabled=True, auto_link=True),
            consolidation=ConsolidationConfig(enabled=True),
            summarization=SummarizationConfig(enabled=True),
            reasoning=ReasoningConfig(enabled=False),
            metacognition=MetacognitionConfig(enabled=False),
            self_learning=SelfLearningConfig(enabled=False),
        )

    def _research_config(self) -> StellarConfig:
        """5-zone, vector index + benchmark."""
        return StellarConfig(
            vector_index=VectorIndexConfig(enabled=True),
            benchmark=BenchmarkConfig(),
            graph=GraphConfig(enabled=False),
            reasoning=ReasoningConfig(enabled=False),
            metacognition=MetacognitionConfig(enabled=False),
            self_learning=SelfLearningConfig(enabled=False),
        )
