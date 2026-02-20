"""OpenAI function calling adapter for Celestial Memory Engine."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from celestial_engine import CelestialMemory


class OpenAIAdapter:
    """Integrates CelestialMemory as OpenAI function calling tools.

    Usage:
        from celestial_engine import CelestialMemory
        from celestial_engine.adapters import OpenAIAdapter

        memory = CelestialMemory()
        adapter = OpenAIAdapter(memory)
        tools = adapter.as_tools()
        # Pass tools to openai.chat.completions.create(tools=tools)
    """

    def __init__(self, memory: CelestialMemory) -> None:
        self._memory = memory

    def as_tools(self) -> list[dict]:
        """Return OpenAI function calling tool definitions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "celestial_store",
                    "description": "Store a memory for later recall",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Memory content to store",
                            },
                            "importance": {
                                "type": "number",
                                "description": "Importance score 0.0-1.0",
                            },
                        },
                        "required": ["content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "celestial_recall",
                    "description": "Recall relevant memories by query",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for memory recall",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
        ]

    def handle_tool_call(self, name: str, arguments: dict) -> str:
        """Handle an OpenAI tool call and return JSON response."""
        if name == "celestial_store":
            item = self._memory.store(
                arguments["content"],
                importance=arguments.get("importance"),
            )
            return json.dumps({"id": item.id, "zone": item.zone, "score": item.total_score})
        elif name == "celestial_recall":
            results = self._memory.recall(
                arguments["query"],
                limit=arguments.get("limit", 5),
            )
            return json.dumps(
                [{"content": r.content, "zone": r.zone, "score": r.total_score} for r in results]
            )
        return json.dumps({"error": f"Unknown tool: {name}"})
