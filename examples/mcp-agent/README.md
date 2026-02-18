# MCP Agent Example

Use Stellar Memory as a memory backend for Claude Code or Cursor.

## Setup

```bash
# Install
pip install stellar-memory[mcp]

# Auto-configure MCP
stellar-memory init-mcp

# Restart Claude Desktop or Cursor
```

## Usage

In Claude Code, try these prompts:

- "Remember that my favorite color is blue" → stores via `memory_store`
- "What's my favorite color?" → recalls via `memory_recall`
- "Show my memory stats" → checks via `memory_stats`
- "Forget about my favorite color" → deletes via `memory_forget`

## How It Works

1. `stellar-memory init-mcp` writes MCP config to your IDE's settings
2. The IDE launches `stellar-memory serve --mcp` as a background process
3. Claude/Cursor can call memory tools (store, recall, forget, stats, etc.)
4. Memories persist in `~/.stellar/memory.db` across sessions

## Custom Database

```bash
stellar-memory init-mcp --db-path ~/my-project/memory.db
```

## Verify Connection

Ask Claude: "Check the memory system health"

Expected: Claude calls `memory_health` and reports the status.
