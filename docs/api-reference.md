# API Reference

## StellarMemory

The main class for interacting with Stellar Memory.

### Constructor

```python
StellarMemory(config: StellarConfig = None, namespace: str = None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | `StellarConfig` | `None` | Configuration object. Uses defaults if `None`. |
| `namespace` | `str` | `None` | Memory namespace for isolation. |

### Core Methods (v3.0 Public API)

| Method | Description | Returns |
|--------|-------------|---------|
| `store(content, importance=0.5, metadata=None, auto_evaluate=False)` | Store a new memory | `MemoryItem` |
| `recall(query, limit=5, emotion=None)` | Search memories by query | `list[MemoryItem]` |
| `get(memory_id)` | Get a specific memory by ID | `MemoryItem \| None` |
| `forget(memory_id)` | Delete a memory | `bool` |
| `reorbit()` | Trigger manual zone rebalancing | `ReorbitResult` |
| `stats()` | Get memory statistics | `MemoryStats` |
| `link(source_id, target_id, relation, weight)` | Link two memories in the knowledge graph | `None` |
| `related(memory_id, depth=2)` | Get memories related through the graph | `list[MemoryItem]` |
| `use(plugin)` | Register a `MemoryPlugin` | `None` |
| `export_json(include_embeddings)` | Export all memories to JSON | `str` |
| `import_json(data)` | Import memories from JSON | `int` |
| `start()` | Start background scheduler | `None` |
| `stop()` | Stop scheduler and clean up | `None` |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `session` | `SessionManager` | Access session management |
| `analyzer` | `GraphAnalyzer \| None` | Access graph analytics |
| `self_learning` | `WeightOptimizer \| None` | Access self-learning module |

### Deprecated Methods (v2.0 compat)

The following methods are still accessible but emit `DeprecationWarning`. Use the plugin system or properties instead:

`health()`, `timeline()`, `narrate()`, `provide_feedback()`, `auto_tune()`, `create_middleware()`, `start_session()`, `end_session()`, `snapshot()`, `graph_stats()`, `graph_communities()`, `graph_centrality()`, `graph_path()`, `encrypt_memory()`, `decrypt_memory()`, `ingest()`, `recall_with_confidence()`, `optimize()`, `rollback_weights()`, `detect_contradictions()`, `benchmark()`

### store()

```python
item = memory.store(
    content="User prefers dark mode",
    importance=0.8,        # 0.0 to 1.0
    metadata={"source": "chat"},
    auto_evaluate=False,   # Use AI to judge importance
)
```

**Returns** `MemoryItem`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique memory ID |
| `content` | `str` | Memory content |
| `zone` | `int` | Current zone (0-4) |
| `total_score` | `float` | Computed importance score |
| `recall_count` | `int` | Number of times recalled |
| `arbitrary_importance` | `float` | Manual importance value |
| `created_at` | `float` | Creation timestamp |
| `emotion` | `EmotionVector \| None` | Emotion analysis result |

### recall()

```python
results = memory.recall(
    query="user preference",
    limit=5,
    emotion="joy",  # optional: filter by emotion
)
```

Returns a list of `MemoryItem` ordered by relevance.

### reorbit()

```python
result = memory.reorbit()
print(f"Moved: {result.moved}, Evicted: {result.evicted}")
```

Forces immediate rebalancing of all memories across zones.

### link()

```python
memory.link(source_id, target_id, relation="related", weight=1.0)
```

Explicitly links two memories in the knowledge graph. Requires `graph.enabled = True`.

### related()

```python
items = memory.related(memory_id, depth=2)
for item in items:
    print(item.content)
```

Returns memories connected through the knowledge graph up to the given depth.

---

## StellarBuilder (v3.0)

The recommended way to create a configured `StellarMemory` instance.

```python
from stellar_memory import StellarBuilder, Preset

memory = StellarBuilder(Preset.CHAT).with_sqlite("chat.db").build()
```

### Presets

| Preset | Description | Use Case |
|--------|-------------|----------|
| `Preset.MINIMAL` | Bare minimum, no optional features | Testing, embedded |
| `Preset.CHAT` | Emotions enabled, session support | Chatbots |
| `Preset.AGENT` | Full features for autonomous agents | AI agents |
| `Preset.KNOWLEDGE` | Graph + summarization optimized | Knowledge bases |
| `Preset.RESEARCH` | All features, high recall limits | Research tools |

### Builder Methods

| Method | Description |
|--------|-------------|
| `.with_sqlite(path)` | Set SQLite database path |
| `.with_memory()` | Use in-memory database |
| `.with_emotions()` | Enable emotion analysis |
| `.with_graph()` | Enable knowledge graph |
| `.with_embedder(model, provider)` | Configure embedding model |
| `.with_llm(provider, model)` | Configure LLM provider |
| `.with_summarization(min_length, max_length)` | Enable summarization |
| `.build()` | Build and return `StellarMemory` instance |

---

## MemoryPlugin (v3.0)

Base class for extending StellarMemory with custom behavior.

```python
from stellar_memory import MemoryPlugin, StellarMemory

class LoggingPlugin(MemoryPlugin):
    def on_store(self, item):
        print(f"Stored: {item.content[:50]}")

    def on_recall(self, query, results):
        print(f"Recalled {len(results)} items for '{query}'")

memory = StellarMemory()
memory.use(LoggingPlugin())
```

### Lifecycle Hooks

| Hook | Trigger | Arguments |
|------|---------|-----------|
| `on_store(item)` | After a memory is stored | `MemoryItem` |
| `on_recall(query, results)` | After a recall query | `str`, `list[MemoryItem]` |
| `on_forget(memory_id)` | After a memory is deleted | `str` |
| `on_reorbit(result)` | After zone rebalancing | `ReorbitResult` |
| `on_consolidate(result)` | After memory consolidation | `ConsolidationResult` |
| `on_decay(result)` | After decay processing | `DecayResult` |
| `on_start()` | When scheduler starts | — |
| `on_stop()` | When scheduler stops | — |
| `on_error(error)` | When an error occurs | `Exception` |

Errors in plugins are isolated — a failing plugin won't crash the system.

---

## Protocol Interfaces (v3.0)

Runtime-checkable interfaces for extending or replacing internal components.

```python
from stellar_memory.protocols import Embedder, Evaluator, StorageBackendProtocol
```

| Protocol | Description | Key Methods |
|----------|-------------|-------------|
| `Embedder` | Text → vector embedding | `embed(text) → list[float]`, `embed_batch(texts)` |
| `Evaluator` | Judge memory importance | `evaluate(content, metadata) → float` |
| `Summarizer` | Summarize memory content | `summarize(content) → str` |
| `StorageBackendProtocol` | Persistent storage backend | `save()`, `load()`, `delete()` |
| `Encryptor` | Memory encryption | `encrypt(data) → bytes`, `decrypt(data) → bytes` |
| `Syncer` | Multi-agent memory sync | `push()`, `pull()` |
| `LLMProvider` | LLM integration | `complete(prompt) → str` |

---

## StellarConfig

Direct configuration (for advanced use). Prefer `StellarBuilder` for most cases.

```python
from stellar_memory import StellarConfig

config = StellarConfig(
    db_path="my_memory.db",
)
memory = StellarMemory(config)
```

### Key Options

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `db_path` | `str` | `"stellar_memory.db"` | SQLite database path |
| `emotion` | `EmotionConfig` | disabled | Emotion analysis settings |
| `zones` | `list[ZoneConfig]` | 5 zones | Zone configuration |
| `memory_function` | `MemoryFunctionConfig` | default weights | Scoring weights |
| `embedder` | `EmbedderConfig` | default | Embedding model settings |
| `llm` | `LLMConfig` | default | LLM provider settings |
| `graph` | `GraphConfig` | enabled | Knowledge graph settings |
| `session` | `SessionConfig` | enabled | Session management |

---

## EmotionVector

6-dimensional emotion analysis result.

| Field | Type | Description |
|-------|------|-------------|
| `joy` | `float` | Joy intensity (0.0-1.0) |
| `sadness` | `float` | Sadness intensity |
| `anger` | `float` | Anger intensity |
| `fear` | `float` | Fear intensity |
| `surprise` | `float` | Surprise intensity |
| `disgust` | `float` | Disgust intensity |
| `dominant` | `str` | Dominant emotion name |
| `intensity` | `float` | Overall emotional intensity |

---

## CLI Commands

```bash
stellar-memory store "content"       # Store a memory
stellar-memory recall "query"        # Search memories
stellar-memory stats                 # Show statistics
stellar-memory health                # Health check
stellar-memory export -o backup.json # Export to JSON
stellar-memory import backup.json    # Import from JSON
stellar-memory forget <id>           # Delete a memory
stellar-memory reorbit               # Trigger rebalancing
stellar-memory serve                 # Start MCP server
stellar-memory serve-api             # Start REST API server
stellar-memory init-mcp              # Generate MCP config
stellar-memory quickstart            # Interactive setup
stellar-memory graph stats           # Graph analytics
```
