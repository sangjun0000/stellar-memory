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

### Core Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `store(content, importance=0.5, metadata=None, auto_evaluate=False)` | Store a new memory | `MemoryItem` |
| `recall(query, limit=5, emotion=None)` | Search memories by query | `list[MemoryItem]` |
| `get(memory_id)` | Get a specific memory by ID | `MemoryItem \| None` |
| `forget(memory_id)` | Delete a memory | `bool` |
| `reorbit()` | Trigger manual zone rebalancing | `ReorbitResult` |
| `stats()` | Get memory statistics | `MemoryStats` |
| `health()` | System health check | `HealthStatus` |

### Advanced Methods

| Method | Description | Since |
|--------|-------------|:-----:|
| `timeline(start, end, limit)` | Time-ordered memory entries | P7 |
| `narrate(topic, limit)` | Generate narrative from memories | P7 |
| `export_json(include_embeddings)` | Export all memories to JSON | P2 |
| `import_json(data)` | Import memories from JSON | P2 |
| `start()` | Start background scheduler | P1 |
| `stop()` | Stop scheduler and clean up | P1 |

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

---

## StellarConfig

Configuration for StellarMemory.

```python
from stellar_memory import StellarConfig, EmotionConfig

config = StellarConfig(
    db_path="my_memory.db",
    emotion=EmotionConfig(enabled=True),
)
```

### Key Options

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `db_path` | `str` | `"stellar_memory.db"` | SQLite database path |
| `emotion` | `EmotionConfig` | disabled | Emotion analysis settings |
| `zones` | `list[ZoneConfig]` | 5 zones | Zone configuration |
| `memory_fn` | `MemoryFunctionConfig` | default weights | Scoring weights |
| `embedder` | `EmbedderConfig` | none | Embedding model settings |
| `llm` | `LLMConfig` | none | LLM provider settings |

### EmotionConfig

```python
EmotionConfig(
    enabled=True,
    weight=0.15,  # weight in memory function
)
```

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
