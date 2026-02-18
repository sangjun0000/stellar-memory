# Stellar Memory

> Give any AI human-like memory. Built on a celestial structure.

Stellar Memory is a Python library that gives any AI system human-like memory capabilities. Inspired by the solar system, memories orbit in 5 zones based on their importance - just like how humans remember important things vividly while less important details gradually fade.

## How It Works

```
        Cloud (Zone 4)    Near-forgotten
        Belt (Zone 3)     Less important
        Outer (Zone 2)    Regular memories
        Inner (Zone 1)    Important memories
        ★ Core (Zone 0)   Always accessible
```

Each memory's position is determined by the **Memory Function**:

```
I(m) = w₁·R(m) + w₂·F(m) + w₃·A(m) + w₄·C(m) + w₅·E(m)
```

- **R(m)**: Recall frequency (log-bounded to prevent overflow)
- **F(m)**: Freshness (decays over time, resets on recall)
- **A(m)**: AI-evaluated importance
- **C(m)**: Graph connectivity (related memories boost each other)
- **E(m)**: Emotional intensity

## Quick Install

```bash
pip install stellar-memory
```

## Next Steps

- [Getting Started](getting-started.md) - Store your first memory in 5 minutes
- [API Reference](api-reference.md) - Full Python API documentation
- [REST API](rest-api.md) - HTTP endpoints with Swagger UI
- [MCP Integration](mcp/claude-code.md) - Connect to Claude Code or Cursor
