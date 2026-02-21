# Design: Platform SDK - Stellar Memory v3.0

> **Feature**: platform-sdk
> **Created**: 2026-02-21
> **Status**: Draft
> **Plan Reference**: `docs/01-plan/features/platform-sdk.plan.md`
> **Version**: v2.0.0 → v3.0.0

---

## 1. Overview

Stellar Memory를 모놀리식 패키지(9,400+ LOC, 58 exports, 33 Config 클래스)에서 **AI 메모리 플랫폼 SDK**로 재구성한다. 핵심 메모리 엔진과 확장 레이어를 분리하여 Homunculus 같은 파생 제품이 깨끗한 SDK를 통해 쉽게 구축할 수 있도록 한다.

### 1.1 Design Goals

1. **Minimal Core**: Public exports 10개 이하, Core ~2,400 LOC
2. **Zero Dependencies**: Core 패키지는 외부 의존성 없음
3. **3-Line Init**: `StellarBuilder(Preset.AGENT).with_sqlite(path).build()`
4. **Plugin-First**: 모든 확장은 플러그인으로 제공
5. **Protocol-Driven**: 파생 제품은 안정적인 Protocol에만 의존

### 1.2 Implementation Order

```
F5 (Protocols) → F4 (Builder) → F3 (Plugin) → F1 (Core SDK) → F2 (Package Split) → F6 (Migration)
```

---

## 2. F5: Interface Contracts (Protocol 정의)

> **Priority**: Step 1 - 모든 것의 기반
> **New File**: `stellar_memory/protocols.py`
> **Estimated LOC**: ~120

### 2.1 MemoryStore Protocol

파생 제품이 의존할 핵심 인터페이스. `StellarMemory`가 이를 구현한다.

```python
# stellar_memory/protocols.py
from __future__ import annotations
from typing import Protocol, runtime_checkable, Any

@runtime_checkable
class MemoryStore(Protocol):
    """Core memory interface for derivative products."""

    def store(self, content: str, *, importance: float = 0.5,
              metadata: dict[str, Any] | None = None) -> str:
        """Store a memory. Returns memory ID."""
        ...

    def recall(self, query: str, *, limit: int = 5,
               min_score: float = 0.0) -> list[MemoryItem]:
        """Recall relevant memories."""
        ...

    def get(self, memory_id: str) -> MemoryItem | None:
        """Get memory by ID."""
        ...

    def forget(self, memory_id: str) -> bool:
        """Delete a memory."""
        ...

    def stats(self) -> MemoryStats:
        """Get memory statistics."""
        ...
```

### 2.2 StorageBackend Protocol

기존 `ZoneStorage(ABC)`를 Protocol로 재정의. 기존 ABC는 하위 호환을 위해 유지하되, 새 구현은 Protocol을 사용.

```python
@runtime_checkable
class StorageBackend(Protocol):
    """Storage extension interface."""

    def store(self, item: MemoryItem) -> None: ...
    def get(self, item_id: str) -> MemoryItem | None: ...
    def get_all(self) -> list[MemoryItem]: ...
    def update(self, item: MemoryItem) -> None: ...
    def remove(self, item_id: str) -> bool: ...
    def search(self, query: str, limit: int = 5,
               query_embedding: list[float] | None = None) -> list[MemoryItem]: ...
    def count(self) -> int: ...
```

### 2.3 EmbedderProvider Protocol

기존 `providers/__init__.py`의 `EmbedderProvider`를 여기로 이동. 기존 위치에는 re-export.

```python
@runtime_checkable
class EmbedderProvider(Protocol):
    """Embedding extension interface."""

    def embed(self, text: str) -> list[float] | None: ...
    def embed_batch(self, texts: list[str]) -> list[list[float] | None]: ...
```

### 2.4 ImportanceEvaluator Protocol

```python
@runtime_checkable
class ImportanceEvaluator(Protocol):
    """Importance evaluation extension interface."""

    def evaluate(self, content: str, metadata: dict[str, Any] | None = None) -> float: ...
```

### 2.5 EventHook Protocol

플러그인 시스템의 기반. 이벤트 타입별 훅을 정의.

```python
@runtime_checkable
class EventHook(Protocol):
    """Event hook for lifecycle integration."""

    def on_event(self, event_type: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Handle an event. Return modified data or None."""
        ...
```

### 2.6 LLMProvider Protocol

기존 `providers/__init__.py`에서 이동.

```python
@runtime_checkable
class LLMProvider(Protocol):
    """LLM provider interface."""

    def complete(self, prompt: str, *, max_tokens: int = 256) -> str: ...
```

### 2.7 Migration Strategy

| Current Location | Action | Destination |
|-----------------|--------|-------------|
| `providers/__init__.py` > `EmbedderProvider` | Move + re-export | `protocols.py` |
| `providers/__init__.py` > `LLMProvider` | Move + re-export | `protocols.py` |
| `storage/__init__.py` > `ZoneStorage(ABC)` | Keep ABC + add Protocol | `protocols.py` (Protocol) |
| `storage/__init__.py` > `StorageBackend(ABC)` | Keep ABC + add Protocol | `protocols.py` (Protocol) |
| (new) `MemoryStore` | Create | `protocols.py` |
| (new) `ImportanceEvaluator` Protocol | Create | `protocols.py` |
| (new) `EventHook` | Create | `protocols.py` |

**하위 호환**: 기존 ABC 기반 코드는 계속 동작. Protocol은 structural subtyping이므로 기존 구현체가 자동으로 호환됨.

---

## 3. F4: SDK Builder

> **Priority**: Step 2
> **New File**: `stellar_memory/builder.py`
> **Estimated LOC**: ~250

### 3.1 Preset Enum

```python
# stellar_memory/builder.py
from enum import Enum

class Preset(Enum):
    """Pre-configured memory profiles."""

    MINIMAL = "minimal"    # Store/Recall only, 3 zones
    CHAT = "chat"          # + Session, Emotion, 5 zones
    AGENT = "agent"        # + Graph, Reasoning, Metacognition, Self-learning
    KNOWLEDGE = "knowledge" # + Graph, Consolidation, Summarization
    RESEARCH = "research"   # + Vector, Benchmark
```

### 3.2 Preset Configurations

각 Preset이 활성화하는 기능:

| Feature | MINIMAL | CHAT | AGENT | KNOWLEDGE | RESEARCH |
|---------|:-------:|:----:|:-----:|:---------:|:--------:|
| Core store/recall | Y | Y | Y | Y | Y |
| 3 zones | Y | - | - | - | - |
| 5 zones | - | Y | Y | Y | Y |
| Session | - | Y | Y | - | - |
| Emotion | - | Y | Y | - | - |
| Graph | - | - | Y | Y | - |
| Reasoning | - | - | Y | - | - |
| Metacognition | - | - | Y | - | - |
| Self-learning | - | - | Y | - | - |
| Consolidation | - | - | - | Y | - |
| Summarization | - | - | - | Y | - |
| Vector Index | - | - | - | - | Y |
| Benchmark | - | - | - | - | Y |

### 3.3 StellarBuilder 클래스

```python
class StellarBuilder:
    """Fluent builder for StellarMemory instances."""

    def __init__(self, preset: Preset = Preset.MINIMAL):
        self._preset = preset
        self._config = self._preset_to_config(preset)
        self._plugins: list[MemoryPlugin] = []
        self._storage_override: StorageBackend | None = None
        self._embedder_override: EmbedderProvider | None = None
        self._evaluator_override: ImportanceEvaluator | None = None

    # === Storage ===

    def with_sqlite(self, path: str) -> StellarBuilder:
        """Use SQLite storage at the given path."""
        self._config.db_path = path
        return self

    def with_postgres(self, dsn: str) -> StellarBuilder:
        """Use PostgreSQL storage."""
        self._config.storage = StorageConfig(backend="postgres", dsn=dsn)
        return self

    def with_storage(self, backend: StorageBackend) -> StellarBuilder:
        """Use a custom storage backend."""
        self._storage_override = backend
        return self

    # === AI Features ===

    def with_embeddings(self, provider: str = "sentence-transformers",
                        model: str | None = None) -> StellarBuilder:
        """Enable semantic search with embeddings."""
        self._config.embedder = EmbedderConfig(
            enabled=True,
            provider=provider,
            model_name=model or "all-MiniLM-L6-v2",
        )
        return self

    def with_embedder(self, embedder: EmbedderProvider) -> StellarBuilder:
        """Use a custom embedder implementation."""
        self._embedder_override = embedder
        return self

    def with_llm(self, provider: str = "anthropic",
                 model: str | None = None) -> StellarBuilder:
        """Enable LLM features (importance evaluation, reasoning)."""
        self._config.llm = LLMConfig(
            enabled=True,
            provider=provider,
            model=model or "claude-haiku-4-5-20251001",
        )
        return self

    # === Intelligence Features ===

    def with_emotions(self, enabled: bool = True) -> StellarBuilder:
        """Enable emotion analysis."""
        self._config.emotion = EmotionConfig(enabled=enabled)
        return self

    def with_graph(self, auto_link: bool = True) -> StellarBuilder:
        """Enable memory graph connections."""
        self._config.graph = GraphConfig(enabled=True, auto_link=auto_link)
        return self

    def with_reasoning(self, enabled: bool = True) -> StellarBuilder:
        """Enable reasoning engine."""
        self._config.reasoning = ReasoningConfig(enabled=enabled)
        return self

    def with_metacognition(self, enabled: bool = True) -> StellarBuilder:
        """Enable metacognition (introspection, confidence)."""
        self._config.metacognition = MetacognitionConfig(enabled=enabled)
        return self

    def with_self_learning(self, enabled: bool = True) -> StellarBuilder:
        """Enable self-learning (pattern collection, weight optimization)."""
        self._config.self_learning = SelfLearningConfig(enabled=enabled)
        return self

    # === Configuration ===

    def with_decay(self, rate: float = 0.01) -> StellarBuilder:
        """Configure decay rate."""
        self._config.memory_function.decay_alpha = rate
        return self

    def with_zones(self, core: int = 20, inner: int = 50,
                   outer: int = 100, belt: int = 200,
                   cloud: int = 500) -> StellarBuilder:
        """Configure zone capacities."""
        capacities = [core, inner, outer, belt, cloud]
        for i, zone in enumerate(self._config.zones):
            if i < len(capacities):
                zone.capacity = capacities[i]
        return self

    def with_namespace(self, namespace: str) -> StellarBuilder:
        """Set namespace for memory isolation."""
        self._namespace = namespace
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
        preset = Preset(data.pop("preset", "minimal"))
        builder = cls(preset)
        # Apply remaining keys to config
        builder._apply_dict(data)
        return builder

    @classmethod
    def from_toml(cls, path: str) -> StellarBuilder:
        """Create builder from a TOML file."""
        import tomllib
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return cls.from_dict(data.get("stellar-memory", data))

    # === Build ===

    def build(self) -> StellarMemory:
        """Build and return a configured StellarMemory instance."""
        from stellar_memory.stellar import StellarMemory

        memory = StellarMemory(
            config=self._config,
            namespace=getattr(self, "_namespace", None),
        )

        # Apply overrides
        if self._storage_override:
            memory._set_storage_backend(self._storage_override)
        if self._embedder_override:
            memory._embedder = self._embedder_override
        if self._evaluator_override:
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
            zones=[
                ZoneConfig(id=0, name="core", capacity=20, importance_min=0.8),
                ZoneConfig(id=1, name="active", capacity=50, importance_min=0.4),
                ZoneConfig(id=2, name="archive", capacity=200, importance_min=0.0),
            ],
            emotion=EmotionConfig(enabled=False),
            graph=GraphConfig(enabled=False),
            reasoning=ReasoningConfig(enabled=False),
            metacognition=MetacognitionConfig(enabled=False),
            self_learning=SelfLearningConfig(enabled=False),
        )

    def _chat_config(self) -> StellarConfig:
        """5-zone, session + emotion."""
        config = StellarConfig()  # default 5 zones
        config.session = SessionConfig(enabled=True)
        config.emotion = EmotionConfig(enabled=True)
        config.graph = GraphConfig(enabled=False)
        config.reasoning = ReasoningConfig(enabled=False)
        return config

    def _agent_config(self) -> StellarConfig:
        """5-zone, full intelligence suite for autonomous agents."""
        config = StellarConfig()
        config.session = SessionConfig(enabled=True)
        config.emotion = EmotionConfig(enabled=True)
        config.graph = GraphConfig(enabled=True, auto_link=True)
        config.reasoning = ReasoningConfig(enabled=True)
        config.metacognition = MetacognitionConfig(enabled=True)
        config.self_learning = SelfLearningConfig(enabled=True)
        return config

    def _knowledge_config(self) -> StellarConfig:
        """5-zone, graph + consolidation + summarization."""
        config = StellarConfig()
        config.graph = GraphConfig(enabled=True, auto_link=True)
        config.consolidation = ConsolidationConfig(enabled=True)
        config.summarization = SummarizationConfig(enabled=True)
        config.reasoning = ReasoningConfig(enabled=False)
        return config

    def _research_config(self) -> StellarConfig:
        """5-zone, vector index + benchmark."""
        config = StellarConfig()
        config.vector_index = VectorIndexConfig(enabled=True)
        config.benchmark = BenchmarkConfig(enabled=True)
        return config
```

### 3.4 Usage Examples

```python
# 1. Minimal (3 lines)
from stellar_memory import StellarBuilder
memory = StellarBuilder().build()

# 2. Preset
from stellar_memory import StellarBuilder, Preset
memory = StellarBuilder(Preset.AGENT).with_sqlite("~/.homunculus/brain.db").build()

# 3. Custom
memory = (
    StellarBuilder()
    .with_sqlite("./memory.db")
    .with_embeddings("openai")
    .with_emotions()
    .with_graph(auto_link=True)
    .with_reasoning()
    .with_decay(rate=0.01)
    .with_zones(core=20, inner=100)
    .with_namespace("homunculus")
    .with_plugin(MyPlugin())
    .build()
)

# 4. From TOML
memory = StellarBuilder.from_toml("stellar.toml").build()
```

---

## 4. F3: Plugin System

> **Priority**: Step 3
> **New File**: `stellar_memory/plugin.py`
> **Estimated LOC**: ~100

### 4.1 MemoryPlugin Base Class

```python
# stellar_memory/plugin.py
from __future__ import annotations
from typing import Any

class MemoryPlugin:
    """Base class for memory plugins.

    Override any hook method to intercept memory lifecycle events.
    All hooks are optional - only override what you need.
    """

    name: str = "unnamed-plugin"

    def on_init(self, memory: StellarMemory) -> None:
        """Called when plugin is registered via memory.use()."""
        pass

    def on_store(self, item: MemoryItem) -> MemoryItem:
        """Called after a memory is stored. Return modified item."""
        return item

    def on_pre_recall(self, query: str, **kwargs) -> str:
        """Called before recall. Return modified query."""
        return query

    def on_recall(self, query: str, results: list[MemoryItem]) -> list[MemoryItem]:
        """Called after recall. Return modified results."""
        return results

    def on_decay(self, item: MemoryItem, new_score: float) -> float:
        """Called during decay calculation. Return adjusted score."""
        return new_score

    def on_reorbit(self, moves: list[tuple[str, int, int]]) -> None:
        """Called after reorbit. moves = [(item_id, old_zone, new_zone)]."""
        pass

    def on_forget(self, memory_id: str) -> bool:
        """Called before forget. Return False to cancel."""
        return True

    def on_consolidate(self, merged_item: MemoryItem,
                       source_items: list[MemoryItem]) -> MemoryItem:
        """Called after consolidation. Return modified merged item."""
        return merged_item

    def on_shutdown(self) -> None:
        """Called when memory.stop() is called."""
        pass
```

### 4.2 PluginManager (Internal)

`StellarMemory` 내부에서 플러그인을 관리하는 private 클래스.

```python
# stellar_memory/_plugin_manager.py (internal)
class PluginManager:
    """Manages registered plugins and dispatches hooks."""

    def __init__(self):
        self._plugins: list[MemoryPlugin] = []

    def register(self, plugin: MemoryPlugin, memory: StellarMemory) -> None:
        """Register a plugin and call on_init."""
        self._plugins.append(plugin)
        plugin.on_init(memory)

    def dispatch_store(self, item: MemoryItem) -> MemoryItem:
        """Chain on_store through all plugins."""
        for plugin in self._plugins:
            item = plugin.on_store(item)
        return item

    def dispatch_pre_recall(self, query: str, **kwargs) -> str:
        """Chain on_pre_recall through all plugins."""
        for plugin in self._plugins:
            query = plugin.on_pre_recall(query, **kwargs)
        return query

    def dispatch_recall(self, query: str,
                        results: list[MemoryItem]) -> list[MemoryItem]:
        """Chain on_recall through all plugins."""
        for plugin in self._plugins:
            results = plugin.on_recall(query, results)
        return results

    def dispatch_decay(self, item: MemoryItem, score: float) -> float:
        """Chain on_decay through all plugins."""
        for plugin in self._plugins:
            score = plugin.on_decay(item, score)
        return score

    def dispatch_reorbit(self, moves: list[tuple[str, int, int]]) -> None:
        """Notify all plugins of reorbit."""
        for plugin in self._plugins:
            plugin.on_reorbit(moves)

    def dispatch_forget(self, memory_id: str) -> bool:
        """Check all plugins allow forget. Any False cancels."""
        for plugin in self._plugins:
            if not plugin.on_forget(memory_id):
                return False
        return True

    def dispatch_consolidate(self, merged: MemoryItem,
                             sources: list[MemoryItem]) -> MemoryItem:
        for plugin in self._plugins:
            merged = plugin.on_consolidate(merged, sources)
        return merged

    def shutdown(self) -> None:
        for plugin in self._plugins:
            plugin.on_shutdown()
```

### 4.3 StellarMemory Integration Points

`stellar.py` 수정 위치:

```python
class StellarMemory:
    def __init__(self, config=None, namespace=None):
        # ... existing init ...
        self._plugin_mgr = PluginManager()

    def use(self, plugin: MemoryPlugin) -> None:
        """Register a plugin."""
        self._plugin_mgr.register(plugin, self)

    def on(self, event: str, callback) -> None:
        """Register event callback (shorthand for EventBus)."""
        self._event_bus.subscribe(event, callback)

    def store(self, content, importance=0.5, metadata=None, ...):
        # ... existing logic ...
        item = self._plugin_mgr.dispatch_store(item)  # ADD
        # ... place in zone ...
        return item

    def recall(self, query, limit=5, ...):
        query = self._plugin_mgr.dispatch_pre_recall(query)  # ADD
        # ... existing search logic ...
        results = self._plugin_mgr.dispatch_recall(query, results)  # ADD
        return results

    def forget(self, memory_id, ...):
        if not self._plugin_mgr.dispatch_forget(memory_id):  # ADD
            return False
        # ... existing delete logic ...

    def stop(self):
        self._plugin_mgr.shutdown()  # ADD
        # ... existing cleanup ...
```

### 4.4 Plugin Example: Homunculus

```python
from stellar_memory import MemoryPlugin, MemoryItem

class HomuculusPlugin(MemoryPlugin):
    name = "homunculus"

    def on_store(self, item: MemoryItem) -> MemoryItem:
        # Classify experience type
        item.metadata = item.metadata or {}
        item.metadata["experience_type"] = self._classify(item.content)
        return item

    def on_recall(self, query: str, results: list[MemoryItem]) -> list[MemoryItem]:
        # Prioritize by personality relevance
        return sorted(results, key=lambda r: self._personality_relevance(r),
                       reverse=True)

    def on_decay(self, item: MemoryItem, new_score: float) -> float:
        # Protect identity memories
        if item.metadata and item.metadata.get("core_identity"):
            return max(new_score, 0.5)
        return new_score

    def _classify(self, content: str) -> str:
        # ... classification logic ...
        return "observation"

    def _personality_relevance(self, item: MemoryItem) -> float:
        # ... relevance scoring ...
        return 0.5
```

---

## 5. F1: Core SDK Layer (StellarMemory Facade 간소화)

> **Priority**: Step 4
> **Modified File**: `stellar_memory/stellar.py`
> **Target**: 961 LOC → ~400 LOC

### 5.1 Public API (v3.0)

**유지 (Core Operations - 14 methods)**:

```python
class StellarMemory:
    # === Core Operations (5) ===
    def store(self, content: str, *, importance: float = 0.5,
              metadata: dict | None = None,
              auto_evaluate: bool = False) -> str:
        """Store a memory. Returns memory ID."""

    def recall(self, query: str, *, limit: int = 5,
               min_score: float = 0.0,
               emotion: str | None = None,
               zone: int | None = None) -> list[MemoryItem]:
        """Recall relevant memories."""

    def get(self, memory_id: str) -> MemoryItem | None:
        """Get a specific memory by ID."""

    def forget(self, memory_id: str) -> bool:
        """Delete a memory."""

    def stats(self) -> MemoryStats:
        """Get memory statistics."""

    # === Lifecycle (3) ===
    def reorbit(self) -> ReorbitResult:
        """Reorganize memories across zones based on scores."""

    def start(self) -> None:
        """Start background scheduler."""

    def stop(self) -> None:
        """Stop background scheduler and cleanup."""

    # === Graph (2) ===
    def link(self, source_id: str, target_id: str,
             relation: str = "related") -> None:
        """Create a link between two memories."""

    def related(self, memory_id: str, depth: int = 2) -> list[MemoryItem]:
        """Find related memories via graph traversal."""

    # === Intelligence (2, optional) ===
    def reason(self, query: str,
               max_sources: int = 5) -> ReasoningResult:
        """Memory-based reasoning. Requires with_reasoning()."""

    def introspect(self, topic: str,
                   depth: int = 1) -> IntrospectionResult:
        """Self-introspection. Requires with_metacognition()."""

    # === Plugin (2) ===
    def use(self, plugin: MemoryPlugin) -> None:
        """Register a plugin."""

    def on(self, event: str, callback: Callable) -> None:
        """Register event callback."""

    # === Serialization (2) ===
    def export_json(self, path: str | None = None,
                    include_embeddings: bool = True) -> str:
        """Export all memories to JSON."""

    def import_json(self, json_str: str) -> int:
        """Import memories from JSON. Returns count."""
```

### 5.2 제거되는 Public Methods

| Method | Migration Path |
|--------|---------------|
| `encrypt_memory()` | `stellar-memory[security]` 플러그인의 `SecurityPlugin.encrypt()` |
| `decrypt_memory()` | `stellar-memory[security]` 플러그인의 `SecurityPlugin.decrypt()` |
| `ingest()` | `stellar-memory[connectors]` 플러그인의 `ConnectorPlugin.ingest()` |
| `create_middleware()` | `StellarBuilder().with_middleware()` 또는 직접 `MemoryMiddleware(memory)` |
| `narrate()` | `memory.stream.narrate()` (stream 모듈 직접 접근) |
| `timeline()` | `memory.stream.timeline()` |
| `benchmark()` | `stellar-memory[dev]`의 `MemoryBenchmark(memory).run()` |
| `provide_feedback()` | 내부 self-learning 자동화 |
| `auto_tune()` | 내부 self-learning 자동화 |
| `graph_stats()` | `memory.graph_analyzer.stats()` |
| `graph_communities()` | `memory.graph_analyzer.communities()` |
| `graph_centrality()` | `memory.graph_analyzer.centrality()` |
| `graph_path()` | `memory.graph_analyzer.find_path()` |
| `recall_with_confidence()` | `recall()`에 통합 (MemoryItem에 `confidence` 필드 추가) |
| `detect_contradictions()` | `reason()`에 통합 |
| `optimize()` | 내부 관리 |
| `snapshot()` | `export_json()`으로 통합 |
| `health()` | `stats()`에 통합 |
| `start_session()` | `memory.session.start()` (session 모듈 직접 접근) |
| `end_session()` | `memory.session.end()` |

### 5.3 Internal Module Access

제거된 메서드의 기능은 내부 모듈에 직접 접근하여 사용 가능:

```python
memory = StellarBuilder(Preset.AGENT).build()

# Graph analytics
memory.graph_analyzer.stats()
memory.graph_analyzer.communities()

# Session management
memory.session.start()
memory.session.end(summarize=True)

# Stream
memory.stream.timeline(limit=50)
memory.stream.narrate("work meetings")

# Self-learning (automatic, but exposed)
memory.self_learning.collect_patterns()
memory.self_learning.optimize_weights()
```

### 5.4 StellarMemory.__init__ 리팩토링

```python
class StellarMemory:
    def __init__(self, config: StellarConfig | None = None,
                 namespace: str | None = None):
        self.config = config or StellarConfig()
        self._namespace = namespace

        # Core (always initialized)
        self._memory_fn = MemoryFunction(self.config.memory_function, self.config.zones)
        self._orbit_mgr = OrbitManager(self.config.zones, StorageFactory(self.config.db_path))
        self._event_bus = EventBus()
        self._plugin_mgr = PluginManager()
        self._embedder = create_embedder(self.config.embedder)

        # Optional modules (lazy or config-gated)
        self._evaluator = self._create_evaluator() if self.config.llm.enabled else NullEvaluator()
        self._scheduler = ReorbitScheduler(self._orbit_mgr, self._memory_fn,
                                           self.config.reorbit_interval)

        # Optional feature modules (exposed as public attributes)
        self.graph_analyzer: GraphAnalyzer | None = None
        self.session: SessionManager | None = None
        self.stream: MemoryStream | None = None
        self.self_learning: SelfLearning | None = None

        self._init_optional_modules()

    def _init_optional_modules(self):
        """Initialize optional modules based on config."""
        if self.config.graph.enabled:
            self._graph = PersistentMemoryGraph(self.config.db_path)
            self.graph_analyzer = GraphAnalyzer(self._graph)

        if self.config.session and self.config.session.enabled:
            self.session = SessionManager(self, self.config.session)

        if hasattr(self.config, 'emotion') and self.config.emotion.enabled:
            self._emotion = EmotionAnalyzer()

        if self.config.reasoning and self.config.reasoning.enabled:
            self._reasoner = MemoryReasoner(self)

        if self.config.metacognition and self.config.metacognition.enabled:
            self._introspector = Introspector(self)

        if self.config.self_learning and self.config.self_learning.enabled:
            self.self_learning = SelfLearning(self, self.config.self_learning)

        self.stream = MemoryStream(self)

    def _set_storage_backend(self, backend: StorageBackend) -> None:
        """Set custom storage backend (used by Builder)."""
        self._orbit_mgr.set_custom_backend(backend)
```

---

## 6. F2: Package Split (pyproject.toml)

> **Priority**: Step 5
> **Modified File**: `pyproject.toml`

### 6.1 New pyproject.toml Structure

```toml
[project]
name = "stellar-memory"
version = "3.0.0"
description = "AI Memory Platform SDK - The Brain for AI Agents"
requires-python = ">=3.10"
dependencies = []  # ZERO external dependencies

[project.optional-dependencies]
# AI Features
embedding = ["sentence-transformers>=2.2.0"]
llm = ["anthropic>=0.18.0"]
openai = ["openai>=1.0.0"]
ollama = ["requests>=2.28.0"]
ai = [
    "sentence-transformers>=2.2.0",
    "anthropic>=0.18.0",
]

# Server & Interfaces
mcp = ["mcp[cli]>=1.2.0"]
server = ["fastapi>=0.110.0", "uvicorn>=0.29.0"]
dashboard = ["fastapi>=0.110.0", "uvicorn>=0.29.0"]

# Storage Backends
postgres = ["asyncpg>=0.29.0"]
redis = ["redis>=5.0.0"]

# Infrastructure
security = ["cryptography>=42.0.0"]
sync = ["websockets>=12.0"]
connectors = ["httpx>=0.27.0"]

# Adapters
adapters = ["langchain-core>=0.1.0"]

# Full install (everything)
full = [
    "stellar-memory[ai,mcp,server,dashboard,postgres,redis,security,sync,connectors,adapters]",
]

# Development
dev = ["pytest>=7.0", "pytest-cov>=4.0", "httpx>=0.27.0"]
docs = ["mkdocs-material>=9.5.0"]
```

### 6.2 Core vs Optional 파일 분류

**Core Package** (항상 포함, Zero Dependencies):

```
stellar_memory/
├── __init__.py           # 10 exports
├── stellar.py            # StellarMemory facade (~400 LOC)
├── builder.py            # StellarBuilder, Preset (NEW)
├── plugin.py             # MemoryPlugin base (NEW)
├── protocols.py          # All Protocols (NEW)
├── config.py             # StellarConfig (~150 LOC, simplified)
├── models.py             # MemoryItem, MemoryStats (~200 LOC)
├── memory_function.py    # Score calculation
├── orbit_manager.py      # Zone management
├── memory_graph.py       # In-memory graph
├── persistent_graph.py   # Graph persistence
├── decay_manager.py      # Decay mechanism
├── adaptive_decay.py     # Adaptive decay
├── event_bus.py          # Event system
├── vector_index.py       # Semantic search
├── utils.py              # cosine_similarity, etc.
├── namespace.py          # Namespace isolation
├── session.py            # Session management
├── storage/
│   ├── __init__.py       # ZoneStorage, StorageFactory
│   ├── in_memory.py      # InMemoryStorage
│   └── sqlite_storage.py # SqliteStorage
├── embedder.py           # Embedder, NullEmbedder
├── importance_evaluator.py  # ImportanceEvaluator, NullEvaluator
├── emotion.py            # EmotionAnalyzer
├── reasoning.py          # MemoryReasoner
├── metacognition.py      # Introspector
├── self_learning.py      # PatternCollector, WeightOptimizer
├── multimodal.py         # ContentTypeHandler
├── stream.py             # MemoryStream
├── graph_analyzer.py     # GraphAnalyzer
├── consolidator.py       # MemoryConsolidator
├── summarizer.py         # MemorySummarizer
└── serializer.py         # Import/Export
```

**Optional Extras** (설치 시에만 포함):

```
stellar_memory/
├── server.py                      # [server] FastAPI REST API
├── mcp_server.py                  # [mcp] MCP server
├── auth.py                        # [server] AuthManager
├── cli.py                         # (keep, simplified)
├── llm_adapter.py                 # [llm] MemoryMiddleware
├── weight_tuner.py                # [llm] WeightTuner
├── storage/
│   ├── postgres_storage.py        # [postgres]
│   └── redis_cache.py             # [redis]
├── providers/
│   ├── __init__.py                # ProviderRegistry
│   ├── openai_provider.py         # [openai]
│   └── ollama_provider.py         # [ollama]
├── adapters/
│   ├── __init__.py
│   ├── langchain.py               # [adapters]
│   └── openai_plugin.py           # [adapters]
├── security/                      # [security]
│   ├── encryption.py
│   ├── access_control.py
│   └── audit.py
├── sync/                          # [sync]
│   ├── sync_manager.py
│   ├── ws_client.py
│   └── ws_server.py
├── connectors/                    # [connectors]
│   ├── api_connector.py
│   ├── web_connector.py
│   └── file_connector.py
├── dashboard/                     # [dashboard]
│   └── app.py
├── event_logger.py                # (keep)
├── benchmark.py                   # [dev]
├── scanner.py                     # [onboard]
├── importer.py                    # [onboard]
├── viz.py                         # [onboard]
└── knowledge_base.py              # [onboard]
```

**완전 제거 (v3.0)**:

```
stellar_memory/
├── billing/                       # REMOVE - SaaS 서버 관심사
│   ├── __init__.py
│   ├── base.py
│   ├── db_models.py
│   ├── tiers.py
│   ├── stripe_provider.py
│   ├── lemonsqueezy.py
│   ├── toss_provider.py
│   └── webhooks.py
```

### 6.3 Lazy Import 전략

Optional extras의 `import` 에러를 방지하기 위한 패턴:

```python
# stellar_memory/stellar.py
class StellarMemory:
    def reason(self, query: str, max_sources: int = 5) -> ReasoningResult:
        """Memory-based reasoning. Requires reasoning to be enabled."""
        if self._reasoner is None:
            raise RuntimeError(
                "Reasoning is not enabled. Use StellarBuilder(Preset.AGENT) "
                "or .with_reasoning() to enable it."
            )
        return self._reasoner.reason(query, max_sources)
```

Optional dependency import 패턴:

```python
# stellar_memory/storage/postgres_storage.py
try:
    import asyncpg
except ImportError:
    raise ImportError(
        "PostgreSQL storage requires asyncpg. "
        "Install with: pip install stellar-memory[postgres]"
    )
```

---

## 7. New __init__.py (v3.0)

> **Target**: 58 exports → 10 exports

### 7.1 Core Exports

```python
# stellar_memory/__init__.py (v3.0)

# 1. Main Class
from .stellar import StellarMemory

# 2. Builder
from .builder import StellarBuilder, Preset

# 3. Core Models
from .models import MemoryItem, MemoryStats

# 4. Plugin Interface
from .plugin import MemoryPlugin

# 5. Extension Protocols
from .protocols import (
    StorageBackend,
    EmbedderProvider,
    ImportanceEvaluator,
    MemoryStore,
)

# 6. Config
from .config import StellarConfig

__version__ = "3.0.0"

__all__ = [
    # Main
    "StellarMemory",
    # Builder
    "StellarBuilder",
    "Preset",
    # Models
    "MemoryItem",
    "MemoryStats",
    # Plugin
    "MemoryPlugin",
    # Protocols
    "StorageBackend",
    "EmbedderProvider",
    "ImportanceEvaluator",
    "MemoryStore",
    # Config
    "StellarConfig",
]
```

**Export count**: 11 (10 + `__version__`)

### 7.2 Backward Compatibility Shim

v2.0 코드와의 호환을 위한 shim 모듈:

```python
# stellar_memory/compat.py (v2 → v3 bridge)
"""
Backward compatibility for v2.0 imports.
Usage: from stellar_memory.compat import *
"""
import warnings

def __getattr__(name):
    """Lazy import with deprecation warning for removed exports."""
    _v2_map = {
        "ScoreBreakdown": (".models", "ScoreBreakdown"),
        "ReorbitResult": (".models", "ReorbitResult"),
        "EvaluationResult": (".models", "EvaluationResult"),
        "FeedbackRecord": (".models", "FeedbackRecord"),
        "EmotionVector": (".emotion", "EmotionVector"),
        "MemoryMiddleware": (".llm_adapter", "MemoryMiddleware"),
        "AnthropicAdapter": (".llm_adapter", "AnthropicAdapter"),
        "EventBus": (".event_bus", "EventBus"),
        "MemoryGraph": (".memory_graph", "MemoryGraph"),
        "VectorIndex": (".vector_index", "VectorIndex"),
        # ... all 58 v2 exports mapped
    }
    if name in _v2_map:
        module_path, attr = _v2_map[name]
        warnings.warn(
            f"Importing {name} from stellar_memory is deprecated. "
            f"Use 'from stellar_memory{module_path} import {attr}' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        import importlib
        module = importlib.import_module(module_path, package="stellar_memory")
        return getattr(module, attr)
    raise AttributeError(f"module 'stellar_memory.compat' has no attribute {name}")
```

---

## 8. F6: celestial_engine 통합

> **Priority**: Step 6
> **Modified**: `celestial_engine/__init__.py`

### 8.1 통합 계획

| celestial_engine Component | Action | Destination |
|---------------------------|--------|-------------|
| `CelestialMemory` | Alias → `StellarMemory` | `celestial_engine/__init__.py` |
| `CelestialMemoryFunction` | Deprecated | Use `MemoryFunction` |
| `ZoneManager` | Deprecated | Use `OrbitManager` |
| `auto_memory.py` (AutoMemory, Presets) | **Merge into Core** | `builder.py` Presets |
| `middleware.py` | Deprecated | Use `llm_adapter.py` |
| `importance.py` (Evaluators) | Deprecated | Use `importance_evaluator.py` |
| `adapters/` | Deprecated | Use `stellar_memory/adapters/` |
| `storage/` | Deprecated | Use `stellar_memory/storage/` |

### 8.2 celestial_engine Deprecation Shim

```python
# celestial_engine/__init__.py (v3.0)
import warnings

warnings.warn(
    "celestial_engine is deprecated. Use stellar_memory instead. "
    "See migration guide: docs/migration-v2-to-v3.md",
    DeprecationWarning,
    stacklevel=2,
)

from stellar_memory import StellarMemory as CelestialMemory
from stellar_memory import StellarBuilder, Preset, StellarConfig
from stellar_memory import MemoryItem, MemoryStats

# Provide all old names as aliases
__all__ = [
    "CelestialMemory",
    "StellarBuilder",
    "Preset",
    "StellarConfig",
    "MemoryItem",
    "MemoryStats",
]
```

### 8.3 AutoMemory → Builder Integration

`celestial_engine/auto_memory.py`의 `AutoMemory` 클래스의 유용한 기능을 `StellarBuilder`에 통합:

```python
# celestial_engine/auto_memory.py 의 핵심 기능:
# - preset-based initialization → StellarBuilder(Preset.AGENT)
# - auto-evaluate on store → .with_auto_evaluate()
# - middleware pattern → .with_middleware()

# 이 기능들은 StellarBuilder에 이미 설계됨
```

---

## 9. Config 간소화

> **Priority**: Step 7 (F1과 병행)
> **Modified File**: `stellar_memory/config.py`
> **Target**: 398 LOC, 33 dataclasses → ~150 LOC, ~10 dataclasses

### 9.1 통합 Config 구조

**Before (v2.0) - 33 dataclasses**:

```
StellarConfig
├── MemoryFunctionConfig
├── ZoneConfig (x5)
├── EmbedderConfig
├── LLMConfig
├── TunerConfig
├── ConsolidationConfig
├── SessionConfig
├── EventConfig
├── NamespaceConfig
├── GraphConfig
├── AdaptiveDecayConfig
├── DecayConfig
├── EventLoggerConfig
├── RecallConfig
├── VectorIndexConfig
├── SummarizationConfig
├── GraphAnalyticsConfig
├── StorageConfig
├── SyncConfig
├── SecurityConfig
├── ConnectorConfig
├── DashboardConfig
├── EmotionConfig
├── ServerConfig
├── BillingConfig          ← REMOVE
├── MetacognitionConfig
├── SelfLearningConfig
├── MultimodalConfig
├── ReasoningConfig
└── BenchmarkConfig
```

**After (v3.0) - ~12 dataclasses**:

```
StellarConfig (simplified)
├── MemoryFunctionConfig   # Core weights (keep)
├── ZoneConfig (x3-5)     # Zone definitions (keep)
├── EmbedderConfig         # Embedding settings (keep, simplified)
├── LLMConfig              # LLM settings (keep)
├── GraphConfig            # Graph settings (enabled + auto_link)
├── EmotionConfig          # Emotion settings (enabled flag)
├── ReasoningConfig        # Reasoning settings (enabled flag)
├── MetacognitionConfig    # Metacognition settings (enabled flag)
├── SelfLearningConfig     # Self-learning settings (enabled flag)
├── SessionConfig          # Session settings (enabled flag)
├── StorageConfig          # Storage backend selection
└── TunerConfig            # Weight tuning (keep)
```

### 9.2 통합되는 Config

| Removed Config | Merged Into |
|---------------|-------------|
| `ConsolidationConfig` | `StellarConfig.consolidation_enabled: bool` |
| `EventConfig` | `StellarConfig.events_enabled: bool` |
| `NamespaceConfig` | `StellarConfig.namespace: str \| None` |
| `AdaptiveDecayConfig` | `MemoryFunctionConfig.adaptive_decay: bool` |
| `DecayConfig` | `MemoryFunctionConfig` (merge fields) |
| `EventLoggerConfig` | `StellarConfig.event_log_path: str \| None` |
| `RecallConfig` | `GraphConfig.recall_boost: bool` |
| `VectorIndexConfig` | `EmbedderConfig.index_type: str` |
| `SummarizationConfig` | `StellarConfig.summarization_enabled: bool` |
| `GraphAnalyticsConfig` | `GraphConfig` (merge fields) |
| `SyncConfig` | Remove (optional extra) |
| `SecurityConfig` | Remove (optional extra) |
| `ConnectorConfig` | Remove (optional extra) |
| `DashboardConfig` | Remove (optional extra) |
| `ServerConfig` | Remove (optional extra) |
| `BillingConfig` | Remove (deleted feature) |
| `BenchmarkConfig` | Remove (dev tool) |
| `MultimodalConfig` | `StellarConfig.multimodal_enabled: bool` |

### 9.3 Simplified StellarConfig

```python
@dataclass
class StellarConfig:
    """Unified configuration for StellarMemory."""

    # Core
    memory_function: MemoryFunctionConfig = field(default_factory=MemoryFunctionConfig)
    zones: list[ZoneConfig] = field(default_factory=_default_zones)
    db_path: str = "stellar_memory.db"
    reorbit_interval: int = 300
    log_level: str = "INFO"
    auto_start_scheduler: bool = True

    # AI
    embedder: EmbedderConfig = field(default_factory=lambda: EmbedderConfig(enabled=False))
    llm: LLMConfig = field(default_factory=lambda: LLMConfig(enabled=False))

    # Intelligence features (enable flags)
    emotion: EmotionConfig = field(default_factory=lambda: EmotionConfig(enabled=False))
    graph: GraphConfig = field(default_factory=lambda: GraphConfig(enabled=False))
    reasoning: ReasoningConfig = field(default_factory=lambda: ReasoningConfig(enabled=False))
    metacognition: MetacognitionConfig = field(default_factory=lambda: MetacognitionConfig(enabled=False))
    self_learning: SelfLearningConfig = field(default_factory=lambda: SelfLearningConfig(enabled=False))
    session: SessionConfig = field(default_factory=lambda: SessionConfig(enabled=False))

    # Storage
    storage: StorageConfig = field(default_factory=StorageConfig)

    # Tuning
    tuner: TunerConfig = field(default_factory=lambda: TunerConfig(enabled=False))

    # Simple flags for minor features
    consolidation_enabled: bool = False
    events_enabled: bool = True
    multimodal_enabled: bool = True
    summarization_enabled: bool = False
    namespace: str | None = None
    event_log_path: str | None = None
```

---

## 10. File Structure (Final v3.0)

```
stellar-memory/
├── stellar_memory/
│   ├── __init__.py                  # 11 exports (NEW)
│   ├── compat.py                    # v2 backward compatibility shim (NEW)
│   ├── stellar.py                   # StellarMemory (~400 LOC, SIMPLIFIED)
│   ├── builder.py                   # StellarBuilder, Preset (NEW ~250 LOC)
│   ├── plugin.py                    # MemoryPlugin base class (NEW ~60 LOC)
│   ├── _plugin_manager.py           # PluginManager internal (NEW ~80 LOC)
│   ├── protocols.py                 # All Protocol interfaces (NEW ~120 LOC)
│   ├── config.py                    # StellarConfig (~150 LOC, SIMPLIFIED)
│   ├── models.py                    # Core models (~200 LOC, SIMPLIFIED)
│   ├── memory_function.py           # Score calculation (unchanged)
│   ├── orbit_manager.py             # Zone management (unchanged)
│   ├── memory_graph.py              # In-memory graph (unchanged)
│   ├── persistent_graph.py          # Graph persistence (unchanged)
│   ├── decay_manager.py             # Decay (unchanged)
│   ├── adaptive_decay.py            # Adaptive decay (unchanged)
│   ├── event_bus.py                 # Event system (unchanged)
│   ├── vector_index.py              # Semantic search (unchanged)
│   ├── utils.py                     # Utilities (unchanged)
│   ├── namespace.py                 # Namespace (unchanged)
│   ├── session.py                   # Session (unchanged)
│   ├── embedder.py                  # Embedder (unchanged)
│   ├── importance_evaluator.py      # Evaluator (unchanged)
│   ├── emotion.py                   # Emotion (unchanged)
│   ├── reasoning.py                 # Reasoning (unchanged)
│   ├── metacognition.py             # Metacognition (unchanged)
│   ├── self_learning.py             # Self-learning (unchanged)
│   ├── multimodal.py                # Content types (unchanged)
│   ├── stream.py                    # Memory stream (unchanged)
│   ├── graph_analyzer.py            # Graph analysis (unchanged)
│   ├── consolidator.py              # Consolidation (unchanged)
│   ├── summarizer.py                # Summarization (unchanged)
│   ├── serializer.py                # Import/export (unchanged)
│   ├── storage/
│   │   ├── __init__.py              # ZoneStorage, StorageFactory
│   │   ├── in_memory.py             # InMemoryStorage
│   │   ├── sqlite_storage.py        # SqliteStorage
│   │   ├── postgres_storage.py      # [postgres]
│   │   └── redis_cache.py           # [redis]
│   ├── providers/                   # [llm/openai/ollama]
│   ├── adapters/                    # [adapters]
│   ├── security/                    # [security]
│   ├── sync/                        # [sync]
│   ├── connectors/                  # [connectors]
│   ├── dashboard/                   # [dashboard]
│   ├── server.py                    # [server]
│   ├── mcp_server.py                # [mcp]
│   ├── auth.py                      # [server]
│   ├── llm_adapter.py               # [llm]
│   ├── weight_tuner.py              # [llm]
│   ├── cli.py                       # Simplified CLI
│   ├── event_logger.py              # JSONL logging
│   ├── benchmark.py                 # [dev]
│   ├── scanner.py                   # [onboard]
│   ├── importer.py                  # [onboard]
│   ├── viz.py                       # [onboard]
│   └── knowledge_base.py            # [onboard]
├── celestial_engine/                # Deprecated shim → stellar_memory
│   └── __init__.py                  # Deprecation warnings + aliases
├── tests/
│   ├── test_builder.py              # NEW: Builder + Preset tests
│   ├── test_plugin.py               # NEW: Plugin system tests
│   ├── test_protocols.py            # NEW: Protocol conformance tests
│   ├── test_compat.py               # NEW: v2 backward compatibility tests
│   └── (기존 테스트 유지)
├── docs/
│   └── migration-v2-to-v3.md        # NEW: Migration guide
└── pyproject.toml                   # v3.0.0
```

---

## 11. Implementation Order (상세)

```
Step 1: F5 - protocols.py                    ~120 LOC  (NEW)
  ↓
Step 2: F4 - builder.py + Preset             ~250 LOC  (NEW)
  ↓
Step 3: F3 - plugin.py + _plugin_manager.py  ~140 LOC  (NEW)
  ↓
Step 4: F1 - stellar.py 리팩토링             ~-560 LOC (MODIFY)
         - 30+ methods → 14 methods
         - Plugin integration points
         - Optional module access pattern
  ↓
Step 5: F1 - __init__.py 정리               ~-134 LOC (MODIFY)
         - 58 exports → 11 exports
         - compat.py 생성
  ↓
Step 6: F1 - config.py 간소화              ~-248 LOC (MODIFY)
         - 33 dataclasses → ~12 dataclasses
  ↓
Step 7: F1 - models.py 간소화              ~-244 LOC (MODIFY)
         - 서버/빌링 관련 모델 제거
  ↓
Step 8: F2 - billing/ 제거                 ~-748 LOC (DELETE)
         - pyproject.toml 업데이트
  ↓
Step 9: F6 - celestial_engine deprecation     ~30 LOC  (MODIFY)
         - AutoMemory 기능 → Builder 통합
  ↓
Step 10: Tests                               ~300 LOC  (NEW)
         - test_builder.py
         - test_plugin.py
         - test_protocols.py
         - test_compat.py
  ↓
Step 11: Migration Guide                      ~100 LOC (NEW)
         - docs/migration-v2-to-v3.md
```

**Net change**: ~-1,500 LOC (코드 감소가 목표)

---

## 12. Test Design

### 12.1 test_protocols.py

| Test | Verification |
|------|-------------|
| `test_stellar_memory_implements_memory_store` | `isinstance(StellarMemory(...), MemoryStore)` |
| `test_sqlite_implements_storage_backend` | `isinstance(SqliteStorage(...), StorageBackend)` |
| `test_embedder_implements_provider` | `isinstance(Embedder(...), EmbedderProvider)` |
| `test_custom_storage_protocol` | Custom class with matching methods passes isinstance |
| `test_protocol_runtime_checkable` | All protocols are `@runtime_checkable` |

### 12.2 test_builder.py

| Test | Verification |
|------|-------------|
| `test_minimal_build` | `StellarBuilder().build()` creates working instance |
| `test_preset_agent` | AGENT preset enables graph, reasoning, metacognition |
| `test_preset_chat` | CHAT preset enables session, emotion |
| `test_preset_knowledge` | KNOWLEDGE preset enables graph, consolidation |
| `test_with_sqlite` | `.with_sqlite(path)` sets db_path |
| `test_with_embeddings` | `.with_embeddings()` enables embedder |
| `test_with_plugin` | `.with_plugin(p)` registers plugin |
| `test_with_zones` | `.with_zones(core=10)` updates zone capacities |
| `test_from_dict` | `StellarBuilder.from_dict({...})` creates correct config |
| `test_from_toml` | `StellarBuilder.from_toml(path)` loads TOML file |
| `test_chained_build` | All builder methods return self (fluent) |
| `test_three_line_init` | `StellarBuilder(Preset.AGENT).with_sqlite(p).build()` works |

### 12.3 test_plugin.py

| Test | Verification |
|------|-------------|
| `test_plugin_on_store_modifies_item` | on_store return value used |
| `test_plugin_on_recall_filters_results` | on_recall modifies results |
| `test_plugin_on_decay_adjusts_score` | on_decay return value used |
| `test_plugin_on_forget_cancels` | on_forget returning False prevents deletion |
| `test_plugin_chain_order` | Multiple plugins called in registration order |
| `test_plugin_on_init_called` | on_init receives StellarMemory reference |
| `test_plugin_on_shutdown_called` | stop() triggers on_shutdown |
| `test_default_plugin_noop` | Base MemoryPlugin methods are no-ops |

### 12.4 test_compat.py

| Test | Verification |
|------|-------------|
| `test_v2_import_with_deprecation` | `from stellar_memory.compat import X` works with warning |
| `test_celestial_engine_deprecated` | `import celestial_engine` shows deprecation |
| `test_celestial_memory_is_stellar` | `CelestialMemory is StellarMemory` |
| `test_v2_config_classes_accessible` | All 33 v2 config classes importable via compat |

---

## 13. Error Handling

| Scenario | Handling |
|----------|---------|
| `reason()` called without `with_reasoning()` | `RuntimeError` with helpful message |
| `introspect()` without `with_metacognition()` | `RuntimeError` with helpful message |
| `pip install stellar-memory[postgres]` missing | `ImportError` with install instructions |
| v2 import path used | `DeprecationWarning` + automatic redirect |
| `celestial_engine` imported | `DeprecationWarning` + alias to `stellar_memory` |
| Plugin raises exception | Log warning, continue (don't crash core) |
| Builder with invalid preset | `ValueError` |
| TOML file not found | `FileNotFoundError` |

---

## 14. Success Criteria

| Criteria | Target | Measurement |
|----------|--------|-------------|
| Core exports | <= 11 | `len(__all__)` |
| Core LOC | ~2,400 | `wc -l` on core files |
| Core import time | < 100ms | `python -c "import timeit; print(timeit.timeit('import stellar_memory', number=100)/100)"` |
| Zero dependencies | 0 | `pip show stellar-memory` |
| 3-line init | Works | `StellarBuilder(Preset.AGENT).with_sqlite(p).build()` |
| Plugin system test coverage | > 80% | `pytest --cov` |
| v2 backward compat | All v2 imports work | `test_compat.py` passes |
| Existing tests pass | >= 90% | `pytest` (excluding billing tests) |
| Homunculus integration | Works | Manual test with v3.0 SDK |

---

## 15. Migration Guide Summary

### For Direct Users (v2.0 → v3.0)

```python
# Before (v2.0)
from stellar_memory import (
    StellarMemory, StellarConfig, MemoryFunctionConfig,
    EmbedderConfig, LLMConfig, ZoneConfig, EmotionConfig,
    GraphConfig, MetacognitionConfig, SelfLearningConfig,
    ReasoningConfig, StorageConfig, EventConfig,
    MemoryItem, EmotionVector, ...
)
config = StellarConfig(
    memory_function=MemoryFunctionConfig(...),
    embedder=EmbedderConfig(...),
    llm=LLMConfig(...),
    zones=[ZoneConfig(...), ZoneConfig(...)],
    emotion=EmotionConfig(...),
    graph=GraphConfig(...),
    metacognition=MetacognitionConfig(...),
    # ... 20+ lines of config
)
memory = StellarMemory(config)

# After (v3.0)
from stellar_memory import StellarBuilder, Preset
memory = (
    StellarBuilder(Preset.AGENT)
    .with_sqlite("~/.myapp/brain.db")
    .with_embeddings()
    .build()
)
```

### For Derivative Products (Homunculus etc.)

```python
# Before: depend on stellar-memory>=2.0.0 (pulls in billing, dashboard, etc.)
# After: depend on stellar-memory>=3.0.0 (core only, zero deps)

from stellar_memory import StellarBuilder, Preset, MemoryPlugin

class MyPlugin(MemoryPlugin):
    name = "my-product"
    def on_store(self, item):
        item.metadata["source"] = "my-product"
        return item

memory = (
    StellarBuilder(Preset.AGENT)
    .with_sqlite(db_path)
    .with_plugin(MyPlugin())
    .build()
)
```

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-21 | Initial design | Claude |
