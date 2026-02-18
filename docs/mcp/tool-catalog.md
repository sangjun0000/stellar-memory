# MCP Tool Catalog

Stellar Memory exposes the following tools via the Model Context Protocol.

## Memory Operations

| Tool | Description | Parameters |
|------|-------------|------------|
| `memory_store` | Store a new memory | `content` (required), `importance` (0.0-1.0), `metadata_json` |
| `memory_recall` | Search memories by query | `query` (required), `limit` (1-20) |
| `memory_get` | Get a specific memory by ID | `memory_id` (required) |
| `memory_forget` | Delete a memory | `memory_id` (required) |

## Management

| Tool | Description | Parameters |
|------|-------------|------------|
| `memory_reorbit` | Trigger zone rebalancing | - |
| `memory_stats` | Get memory statistics | - |
| `memory_health` | System health check | - |
| `memory_export` | Export memories to JSON | `include_embeddings` (bool) |
| `memory_import` | Import memories from JSON | `data` (JSON string) |

## Graph

| Tool | Description | Parameters |
|------|-------------|------------|
| `memory_graph_neighbors` | Find related memories | `memory_id`, `depth` (1-3) |
| `memory_graph_communities` | Detect memory clusters | - |
| `memory_graph_path` | Find path between memories | `source`, `target` |

## Example Interactions

### Storing a Memory

User: "Remember that the project deadline is March 15th"

Claude calls:
```json
{
  "tool": "memory_store",
  "arguments": {
    "content": "Project deadline is March 15th",
    "importance": 0.9
  }
}
```

### Recalling Memories

User: "What do you know about project deadlines?"

Claude calls:
```json
{
  "tool": "memory_recall",
  "arguments": {
    "query": "project deadline",
    "limit": 5
  }
}
```

### Checking Stats

User: "How many things do you remember?"

Claude calls:
```json
{
  "tool": "memory_stats",
  "arguments": {}
}
```
