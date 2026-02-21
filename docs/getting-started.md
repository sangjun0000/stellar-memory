# Getting Started

Store your first memory in under 5 minutes.

## Step 1: Install (30 seconds)

```bash
pip install stellar-memory
```

## Step 2: Store a Memory (1 minute)

```python
from stellar_memory import StellarMemory

memory = StellarMemory()
item = memory.store("Hello, Stellar Memory!", importance=0.8)
print(f"Stored in Zone {item.zone}")  # Zone 0 (Core) - high importance
```

## Step 3: Recall (1 minute)

```python
results = memory.recall("hello")
print(results[0].content)  # "Hello, Stellar Memory!"
```

## Step 4: Check Statistics (30 seconds)

```python
stats = memory.stats()
print(f"Total: {stats.total_memories} memories")
for zone_id, count in sorted(stats.zone_counts.items()):
    print(f"  Zone {zone_id}: {count}")
```

## Step 5: Use the Builder (v3.0)

The recommended way to configure Stellar Memory:

```python
from stellar_memory import StellarBuilder, Preset

# Choose a preset that fits your use case
memory = StellarBuilder(Preset.CHAT).with_sqlite("chat.db").build()

item = memory.store("Got my first customer today!")
print(f"Stored: {item.content}")
```

Available presets: `MINIMAL`, `CHAT`, `AGENT`, `KNOWLEDGE`, `RESEARCH`.

## Step 6: Link Related Memories

```python
id1 = memory.store("Python is my favorite language", importance=0.8).id
id2 = memory.store("I use FastAPI for web APIs", importance=0.7).id

# Explicitly link related memories
memory.link(id1, id2, relation="related")

# Discover related memories through the graph
related = memory.related(id1)
for item in related:
    print(f"  Related: {item.content}")
```

## Step 7: Clean Up

```python
memory.stop()
```

## Next Steps

Choose your path:

- **Python library** - See [API Reference](api-reference.md) for all methods
- **REST API** - Run `stellar-memory serve-api` and open `http://localhost:9000/docs`
- **MCP Server** - Run `stellar-memory init-mcp` for Claude Code/Cursor integration
- **Docker** - Run `docker-compose up stellar` for containerized deployment
- **Migration from v2** - See [Migration Guide](migration-v2-to-v3.md) for upgrading

## Interactive Setup

For a guided setup experience:

```bash
stellar-memory quickstart
```

This wizard walks you through choosing a usage mode, configuring options, and storing your first memory.
