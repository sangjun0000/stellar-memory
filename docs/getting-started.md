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

## Step 5: Emotional Memory (1 minute)

```python
from stellar_memory import StellarConfig, EmotionConfig

config = StellarConfig(emotion=EmotionConfig(enabled=True))
memory = StellarMemory(config)

item = memory.store("Got my first customer today!")
if item.emotion:
    print(f"Dominant emotion: {item.emotion.dominant}")
    print(f"Joy: {item.emotion.joy:.2f}")
```

## Step 6: Clean Up

```python
memory.stop()
```

## Next Steps

Choose your path:

- **Python library** - See [API Reference](api-reference.md) for all methods
- **REST API** - Run `stellar-memory serve-api` and open `http://localhost:9000/docs`
- **MCP Server** - Run `stellar-memory init-mcp` for Claude Code/Cursor integration
- **Docker** - Run `docker-compose up stellar` for containerized deployment

## Interactive Setup

For a guided setup experience:

```bash
stellar-memory quickstart
```

This wizard walks you through choosing a usage mode, configuring options, and storing your first memory.
