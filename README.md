# Stellar Memory

> Give any AI human-like memory. Built on a celestial structure.

[![PyPI](https://img.shields.io/pypi/v/stellar-memory)](https://pypi.org/project/stellar-memory/)
[![Tests](https://img.shields.io/github/actions/workflow/status/stellar-memory/stellar-memory/ci.yml?label=tests)](https://github.com/stellar-memory/stellar-memory/actions)
[![Python](https://img.shields.io/pypi/pyversions/stellar-memory)](https://pypi.org/project/stellar-memory/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

```
        Cloud (Zone 4) - Near-forgotten
       ╱                              ╲
      Belt (Zone 3) - Less important
     ╱                                ╲
    Outer (Zone 2) - Regular memories
   ╱                                    ╲
  Inner (Zone 1) - Important memories
 ╱                                        ╲
         ★ Core (Zone 0) ★
         Most important memories
         Always accessible
```

## Why Stellar Memory?

| | Traditional AI | With Stellar Memory |
|---|---|---|
| Memory | Forgets after context window | Remembers across sessions |
| Importance | Treats all info equally | Ranks by importance score |
| Organization | Flat key-value store | 5-zone celestial hierarchy |
| Forgetting | Manual deletion only | Adaptive decay, like humans |

## Quick Start

```python
from stellar_memory import StellarMemory

memory = StellarMemory()

# Store memories with different importance
memory.store("User prefers dark mode", importance=0.8)
memory.store("The weather is nice today", importance=0.2)
memory.store("Project deadline is March 1st", importance=0.9)

# Recall relevant memories
results = memory.recall("user preference")
print(results[0].content)  # "User prefers dark mode"

# Check statistics
stats = memory.stats()
print(f"Total: {stats.total_memories} memories across 5 zones")

memory.stop()
```

## Installation

```bash
# Core library (zero dependencies)
pip install stellar-memory

# With REST API server
pip install stellar-memory[server]

# With MCP server (Claude Code / Cursor)
pip install stellar-memory[mcp]

# Everything
pip install stellar-memory[full]
```

**Requirements**: Python 3.10+

## Key Features

- **5-Zone Memory Hierarchy** - Solar system model: Core, Inner, Outer, Belt, Cloud
- **Black Hole Prevention** - Logarithmic recall function prevents memory overflow
- **Emotional Memory** - 6-dimensional emotion vectors (joy, sadness, anger, fear, surprise, disgust)
- **Memory Function** - `I(m) = w₁·R(m) + w₂·F(m) + w₃·A(m) + w₄·C(m) + w₅·E(m)`
- **MCP Server** - Claude Code and Cursor integration via Model Context Protocol
- **REST API** - FastAPI with Swagger UI and ReDoc
- **Graph Analytics** - Memory relationships, communities, centrality analysis
- **Multi-Agent Sync** - CRDT-based conflict resolution + WebSocket
- **Adaptive Decay** - Human-like forgetting with reinforcement on recall
- **LangChain / OpenAI Adapters** - Drop-in integrations

## Use Cases

- **AI Chatbot** - Persistent memory across conversations
- **Personal Assistant** - Learn user preferences over time
- **Code Assistant** - Remember project context and decisions
- **Knowledge Management** - Organize and retrieve information naturally

## Four Ways to Use

### 1. Python Library

```python
from stellar_memory import StellarMemory, StellarConfig, EmotionConfig

config = StellarConfig(emotion=EmotionConfig(enabled=True))
memory = StellarMemory(config)

item = memory.store("Got promoted today!", importance=0.9)
print(f"Emotion: {item.emotion.dominant}")  # "joy"
```

### 2. REST API

```bash
stellar-memory serve-api
# Open http://localhost:9000/docs for Swagger UI
```

```bash
curl -X POST http://localhost:9000/api/v1/store \
  -H "Content-Type: application/json" \
  -d '{"content": "Remember this", "importance": 0.7}'
```

### 3. MCP Server (Claude Code / Cursor)

```bash
stellar-memory init-mcp --ide claude
# Restart Claude Desktop - memory tools are now available
```

### 4. Docker

```bash
docker-compose up stellar
# API available at http://localhost:9000
```

## Architecture

The memory function determines where each memory lives:

```
I(m) = w₁·R(m) + w₂·F(m) + w₃·A(m) + w₄·C(m) + w₅·E(m)

R(m) = log(1 + recall_count)     # Recall (log-bounded)
F(m) = -α · time_since_recall    # Freshness (decays, resets on recall)
A(m) = ai_evaluated_importance   # Arbitrary importance (AI-judged)
C(m) = connection_strength       # Graph connectivity
E(m) = emotional_intensity       # Emotion weight
```

Memories are periodically **reorbited** - moved between zones based on their total score. High-scoring memories migrate toward the Core; low-scoring ones drift to the Cloud and eventually evaporate.

## Documentation

- [Getting Started](https://stellar-memory.readthedocs.io/getting-started/)
- [API Reference](https://stellar-memory.readthedocs.io/api-reference/)
- [REST API](https://stellar-memory.readthedocs.io/rest-api/)
- [MCP Integration](https://stellar-memory.readthedocs.io/mcp/claude-code/)
- [Guides](https://stellar-memory.readthedocs.io/guides/chatbot/)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
