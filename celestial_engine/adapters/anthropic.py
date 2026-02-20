"""Anthropic/Claude MCP adapter for Celestial Memory Engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from celestial_engine import CelestialMemory


class AnthropicAdapter:
    """Integrates CelestialMemory as Claude MCP tools.

    Usage:
        from celestial_engine import CelestialMemory
        from celestial_engine.adapters import AnthropicAdapter

        memory = CelestialMemory()
        adapter = AnthropicAdapter(memory)
        tools = adapter.as_mcp_tools()
    """

    def __init__(self, memory: CelestialMemory) -> None:
        self._memory = memory

    def as_mcp_tools(self) -> list[dict]:
        """Return MCP tool definitions."""
        return [
            {
                "name": "celestial_store",
                "description": "Store a memory in the celestial memory system",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "importance": {"type": "number"},
                    },
                    "required": ["content"],
                },
            },
            {
                "name": "celestial_recall",
                "description": "Recall memories from the celestial memory system",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["query"],
                },
            },
        ]

    def handle(self, tool_name: str, tool_input: dict) -> dict:
        """Handle an MCP tool call."""
        if tool_name == "celestial_store":
            item = self._memory.store(
                tool_input["content"],
                importance=tool_input.get("importance"),
            )
            return {"id": item.id, "zone": item.zone, "score": item.total_score}
        elif tool_name == "celestial_recall":
            results = self._memory.recall(
                tool_input["query"],
                limit=tool_input.get("limit", 5),
            )
            return {
                "memories": [
                    {"content": r.content, "zone": r.zone, "score": r.total_score}
                    for r in results
                ]
            }
        return {"error": f"Unknown tool: {tool_name}"}
