# Cursor MCP Setup

Connect Stellar Memory to Cursor as a persistent memory backend.

## Quick Setup

```bash
pip install stellar-memory[mcp]
stellar-memory init-mcp --ide cursor
```

Restart Cursor to activate Stellar Memory tools.

## Manual Setup

Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "stellar-memory": {
      "command": "stellar-memory",
      "args": ["serve", "--mcp"],
      "env": {
        "STELLAR_DB_PATH": "~/.stellar/memory.db"
      }
    }
  }
}
```

## Verify

In Cursor chat, try:

- "Remember this project uses React 19" → calls `memory_store`
- "What do you know about this project?" → calls `memory_recall`

## Available Tools

See [Tool Catalog](tool-catalog.md) for all available MCP tools.
