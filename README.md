# Stellar Memory

> Give your AI the ability to remember. Free & open-source.

[![PyPI](https://img.shields.io/pypi/v/stellar-memory)](https://pypi.org/project/stellar-memory/)
[![Tests](https://img.shields.io/github/actions/workflow/status/sangjun0000/stellar-memory/ci.yml?label=tests)](https://github.com/sangjun0000/stellar-memory/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## What is Stellar Memory?

Stellar Memory gives any AI the ability to remember things across conversations.
Once your AI learns something about you, it remembers it next time — just like a person.

**No programming required.** Works with Claude Desktop, Cursor, and any MCP-compatible AI.

## Get Started (2 options)

### Option 1: Install on your computer (Recommended)

**Windows:**
1. Download [`stellar-memory-setup.bat`](https://github.com/sangjun0000/stellar-memory/releases/latest)
2. Double-click to run
3. Restart Claude Desktop or Cursor
4. Done! Try saying: "Remember my name is ___"

**macOS / Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/sangjun0000/stellar-memory/main/stellar-memory-setup.sh | bash
```

**Or if you have Python:**
```bash
pip install stellar-memory[mcp]
stellar-memory setup
```

### Option 2: Use in the cloud

Cloud service coming soon. You'll be able to use Stellar Memory from any browser without installing anything.

For now, developers can use the REST API — see [API docs](https://stellar-memory.com/docs/api-reference/).

## How it works

```
You: "My favorite color is blue. Remember that."
AI:  "Got it! I'll remember that your favorite color is blue."

... next conversation ...

You: "What's my favorite color?"
AI:  "Your favorite color is blue!"
```

Stellar Memory organizes memories like a solar system:
- **Core** — Most important, always remembered
- **Inner** — Important, frequently accessed
- **Outer** — Regular memories
- **Belt** — Less important
- **Cloud** — Rarely accessed, may fade

## For Developers

<details>
<summary>Click to expand developer documentation</summary>

### Python Library

```python
from stellar_memory import StellarMemory

memory = StellarMemory()
memory.store("User prefers dark mode", importance=0.8)
results = memory.recall("user preferences")
memory.stop()
```

### Installation Options

```bash
pip install stellar-memory          # Core library
pip install stellar-memory[mcp]     # With MCP server
pip install stellar-memory[server]  # With REST API
pip install stellar-memory[full]    # Everything
```

### Key Features

- **5-Zone Hierarchy** — Core, Inner, Outer, Belt, Cloud
- **Adaptive Decay** — Memories naturally fade like human memory
- **Emotion Engine** — 6-dimensional emotion vectors
- **Self-Learning** — Optimizes based on usage patterns
- **MCP Server** — Claude Code, Cursor integration
- **REST API** — Full HTTP API with Swagger docs
- **Vector Search** — Semantic similarity matching
- **Graph Analytics** — Memory relationships and communities
- **Multi-Agent Sync** — CRDT-based conflict resolution

### Requirements

Python 3.10+

### Documentation

- [Full Documentation](https://stellar-memory.com/docs/)
- [API Reference](https://stellar-memory.com/docs/api-reference/)
- [Examples](https://github.com/sangjun0000/stellar-memory/tree/main/examples)

</details>

## License

MIT License — free to use, modify, and distribute.
