# Migration Guide: v2.0 to v3.0

## Overview

Stellar Memory v3.0 is a major release that restructures the package as an **AI Memory Platform SDK**. The public API has been simplified from 36+ methods to 16 core methods, and a new Builder pattern replaces manual configuration.

All v2.0 imports continue to work with deprecation warnings. No breaking changes at the import level.

## Quick Start (v3.0)

```python
from stellar_memory import StellarBuilder, Preset

# 3-line init replaces manual StellarConfig construction
memory = StellarBuilder(Preset.MINIMAL).with_memory().build()

# Core API (unchanged)
item = memory.store("hello world", importance=0.8)
results = memory.recall("hello")
memory.forget(item.id)
memory.stop()
```

## Import Changes

### Package-level imports (11 core exports)

```python
# v3.0 core imports (no warnings)
from stellar_memory import (
    StellarMemory,
    StellarBuilder, Preset,
    MemoryItem, MemoryStats,
    MemoryPlugin,
    StorageBackendProtocol, EmbedderProvider,
    ImportanceEvaluator, MemoryStore,
    StellarConfig,
)
```

### v2.0 imports (still work, deprecation warning)

```python
# These still work but produce DeprecationWarning:
from stellar_memory import EventBus          # -> from stellar_memory.event_bus import EventBus
from stellar_memory import MemoryFunctionConfig  # -> from stellar_memory.config import ...
from stellar_memory import ScoreBreakdown    # -> from stellar_memory.models import ...
```

### Direct module imports (no warnings)

```python
# Direct imports always work without warnings:
from stellar_memory.config import MemoryFunctionConfig
from stellar_memory.models import ScoreBreakdown
from stellar_memory.event_bus import EventBus
```

## API Changes

### Builder Pattern (NEW)

```python
# v2.0: Manual config construction
from stellar_memory import StellarMemory, StellarConfig
from stellar_memory.config import GraphConfig, EmotionConfig
config = StellarConfig(
    db_path=":memory:",
    graph=GraphConfig(enabled=True),
    emotion=EmotionConfig(enabled=True),
)
memory = StellarMemory(config)

# v3.0: Builder with presets
from stellar_memory import StellarBuilder, Preset
memory = StellarBuilder(Preset.CHAT).with_memory().build()
# Or customize:
memory = (
    StellarBuilder()
    .with_sqlite("my.db")
    .with_graph(threshold=0.6)
    .with_emotions()
    .build()
)
```

### Presets

| Preset | Features |
|--------|----------|
| `MINIMAL` | 3 zones, all extras off |
| `CHAT` | Session + emotion |
| `AGENT` | Full intelligence (graph, reasoning, metacognition, self-learning) |
| `KNOWLEDGE` | Graph + consolidation + summarization |
| `RESEARCH` | Vector index + benchmarking |

### Method Changes

| v2.0 Method | v3.0 Replacement | Notes |
|-------------|------------------|-------|
| `recall_graph()` | `related()` | Same behavior, clearer name |
| `graph_stats()` | `memory.graph_analyzer.stats()` | Access via property |
| `graph_communities()` | `memory.graph_analyzer.communities()` | Access via property |
| `graph_centrality()` | `memory.graph_analyzer.centrality()` | Access via property |
| `graph_path()` | `memory.graph_analyzer.find_path()` | Access via property |
| `start_session()` | `memory.session_manager.start_session()` | Access via property |
| `end_session()` | `memory.session_manager.end_session()` | Access via property |
| `timeline()` | `memory.stream.timeline()` | Access via property |
| `narrate()` | `memory.stream.narrate()` | Access via property |
| `health()` | `stats()` | Merged into stats |
| NEW: `link()` | - | Explicit graph linking |
| NEW: `related()` | - | Graph traversal |
| NEW: `use()` | - | Register plugin |

### v3.0 Core Public API (16 methods)

```python
memory.store(content, importance=0.5)  # Store a memory
memory.recall(query, limit=5)          # Recall memories
memory.get(memory_id)                  # Get by ID
memory.forget(memory_id)               # Delete a memory
memory.stats()                         # System statistics
memory.reorbit()                       # Manual reorbit cycle
memory.link(source_id, target_id)      # Link memories in graph
memory.related(memory_id, depth=2)     # Get related memories
memory.use(plugin)                     # Register a plugin
memory.on(event, callback)             # Subscribe to events
memory.export_json()                   # Export all memories
memory.import_json(json_str)           # Import memories
memory.reason(query)                   # AI reasoning over memories
memory.introspect(topic)               # Knowledge state analysis
memory.start()                         # Start scheduler
memory.stop()                          # Stop and cleanup
```

## Plugin System (NEW)

```python
from stellar_memory import MemoryPlugin

class MyPlugin(MemoryPlugin):
    name = "my-plugin"

    def on_store(self, item):
        item.metadata["processed"] = True
        return item

    def on_recall(self, query, results):
        return [r for r in results if r.total_score > 0.3]

memory.use(MyPlugin())
```

### Plugin Hooks

| Hook | When | Return |
|------|------|--------|
| `on_init(memory)` | Plugin registered | - |
| `on_store(item)` | After store | MemoryItem |
| `on_pre_recall(query)` | Before recall search | str |
| `on_recall(query, results)` | After recall | list |
| `on_decay(item, score)` | During decay | float |
| `on_reorbit(moves)` | After reorbit | - |
| `on_forget(memory_id)` | Before forget | bool (False cancels) |
| `on_consolidate(merged, sources)` | During merge | MemoryItem |
| `on_shutdown()` | On stop() | - |

## Protocol Interfaces (NEW)

```python
from stellar_memory import StorageBackendProtocol, EmbedderProvider

class MyStorage:
    """Custom storage that conforms to StorageBackendProtocol."""
    def store(self, item): ...
    def get(self, item_id): ...
    def get_all(self): ...
    def update(self, item): ...
    def remove(self, item_id): ...
    def search(self, query, limit=5, query_embedding=None): ...
    def count(self): ...

assert isinstance(MyStorage(), StorageBackendProtocol)  # True
```

## celestial_engine Package

The `celestial_engine` package is deprecated. It now re-exports from `stellar_memory`:

```python
# v2.0 (deprecated, produces warning)
from celestial_engine import CelestialMemory
memory = CelestialMemory()

# v3.0
from stellar_memory import StellarBuilder, Preset
memory = StellarBuilder(Preset.MINIMAL).with_sqlite("celestial_memory.db").build()
```

## Removed in v3.0

- `BillingConfig` - Moved to external billing package
- `OnboardConfig` / `KnowledgeBaseConfig` - Moved to external onboarding package
- `billing/` directory - Use external billing integration
- Smart Onboarding models (`ScanResult`, `ScanSummary`, `ImportResult`, `ChunkInfo`) - Moved to external package

## Timeline

- **v3.0**: All v2.0 imports work with deprecation warnings
- **v3.1** (planned): Deprecation warnings become errors for removed classes
- **v4.0** (planned): v2.0 compat layer removed
