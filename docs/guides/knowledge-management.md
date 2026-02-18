# Knowledge Management

Use Stellar Memory as a personal or team knowledge base with natural language retrieval.

## Setup

```python
from stellar_memory import StellarMemory, StellarConfig

config = StellarConfig(db_path="knowledge.db")
memory = StellarMemory(config)
```

## Storing Knowledge

```python
# Store facts with appropriate importance
memory.store("Python 3.12 introduced type parameter syntax (PEP 695)", importance=0.7)
memory.store("Docker multi-stage builds reduce image size by 60-80%", importance=0.6)
memory.store("CRDT (Conflict-free Replicated Data Type) enables offline-first sync", importance=0.8)
```

## Natural Language Search

```python
results = memory.recall("how to reduce docker image size")
for item in results:
    print(f"[Zone {item.zone}] {item.content}")
```

## Graph-Based Discovery

Find related knowledge through memory connections:

```python
# Store related items
id1 = memory.store("FastAPI uses Pydantic for validation", importance=0.7).id
id2 = memory.store("Pydantic v2 is 5-50x faster than v1", importance=0.6).id

# Later, discover connections via graph
if memory._analyzer:
    neighbors = memory._analyzer.neighbors(id1, depth=2)
```

## Export and Backup

```python
# Export all knowledge
data = memory.export_json()
with open("knowledge_backup.json", "w") as f:
    f.write(data)

# Import on another machine
with open("knowledge_backup.json") as f:
    count = memory.import_json(f.read())
print(f"Imported {count} memories")
```

## REST API Access

Start the server for team access:

```bash
stellar-memory serve-api --db knowledge.db
```

Team members can query via HTTP:

```bash
curl "http://localhost:9000/api/v1/recall?q=docker+optimization&limit=5"
```

## Cleanup

```python
memory.stop()
```
