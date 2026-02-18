# Claude Code MCP Setup

Connect Stellar Memory to Claude Code as a persistent memory backend.

## Quick Setup (Recommended)

```bash
pip install stellar-memory[mcp]
stellar-memory init-mcp --ide claude
```

Restart Claude Desktop to activate Stellar Memory tools.

## Manual Setup

Edit your Claude Desktop config file:

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/claude/claude_desktop_config.json` |

Add the following:

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

In Claude Code, try:

- "What do you remember about me?" → calls `memory_recall`
- "Remember that I prefer TypeScript" → calls `memory_store`
- "Show memory stats" → calls `memory_stats`

## Custom Database Path

```bash
stellar-memory init-mcp --ide claude --db-path ~/my-project/memory.db
```

## Dry Run

Preview the config without writing:

```bash
stellar-memory init-mcp --dry-run
```

## Available Tools

Once connected, Claude Code can use all [MCP tools](tool-catalog.md) including:

- `memory_store` - Store new memories
- `memory_recall` - Search and retrieve memories
- `memory_forget` - Delete memories
- `memory_stats` - View statistics
- `memory_health` - Check system health

See [Tool Catalog](tool-catalog.md) for the complete list.
