# Code Assistant with Memory

Build a code assistant that remembers project context, decisions, and patterns.

## Setup

```python
from stellar_memory import StellarMemory, StellarConfig

config = StellarConfig(db_path="code_assistant_memory.db")
memory = StellarMemory(config)
```

## Storing Project Context

```python
# Store architectural decisions
memory.store(
    "Project uses FastAPI for REST endpoints and SQLAlchemy for ORM",
    importance=0.9,
    metadata={"type": "architecture"},
)

# Store coding conventions
memory.store(
    "All API responses use Pydantic models with Field descriptions",
    importance=0.8,
    metadata={"type": "convention"},
)

# Store bug fixes for reference
memory.store(
    "Fixed: Unicode regex in emotion.py needed re.UNICODE flag for Korean text",
    importance=0.7,
    metadata={"type": "bugfix", "file": "emotion.py"},
)
```

## Retrieving Relevant Context

```python
def get_context_for_task(task_description: str) -> str:
    results = memory.recall(task_description, limit=10)
    context = []
    for item in results:
        meta = item.metadata or {}
        tag = meta.get("type", "note")
        context.append(f"[{tag}] {item.content}")
    return "\n".join(context)

context = get_context_for_task("add a new API endpoint")
# Returns relevant architecture decisions and conventions
```

## MCP Integration for IDE

Connect directly to Claude Code or Cursor:

```bash
stellar-memory init-mcp --db-path ./code_assistant_memory.db
```

Now the AI in your IDE can store and recall project knowledge automatically.

## Cleanup

```python
memory.stop()
```
