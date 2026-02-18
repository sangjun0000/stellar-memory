"""OpenAI function calling schema for Stellar Memory."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.stellar import StellarMemory


STELLAR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "memory_store",
            "description": "Store a new memory for future recall",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Memory content to store",
                    },
                    "importance": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
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
            "name": "memory_recall",
            "description": "Search memories by query",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 20,
                        "description": "Max results",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_forget",
            "description": "Delete a specific memory by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "Memory UUID",
                    },
                },
                "required": ["memory_id"],
            },
        },
    },
]


class OpenAIMemoryPlugin:
    """Plugin that handles OpenAI function call dispatch.

    Usage::

        from stellar_memory import StellarMemory
        from stellar_memory.adapters.openai_plugin import OpenAIMemoryPlugin, STELLAR_TOOLS

        memory = StellarMemory()
        plugin = OpenAIMemoryPlugin(memory)
        result = plugin.handle_call("memory_store", '{"content": "hello"}')
    """

    def __init__(self, stellar_memory: StellarMemory):
        self._memory = stellar_memory

    def get_tools(self) -> list[dict]:
        """Return OpenAI tools schema."""
        return STELLAR_TOOLS

    def handle_call(self, function_name: str, arguments: str) -> str:
        """Dispatch function call and return JSON result."""
        args = json.loads(arguments)

        if function_name == "memory_store":
            item = self._memory.store(
                content=args["content"],
                importance=args.get("importance", 0.5),
                auto_evaluate=True,
            )
            return json.dumps({"id": item.id, "zone": item.zone})

        elif function_name == "memory_recall":
            results = self._memory.recall(
                args["query"], limit=args.get("limit", 5)
            )
            return json.dumps([{
                "id": item.id, "content": item.content,
                "zone": item.zone, "importance": item.arbitrary_importance,
            } for item in results])

        elif function_name == "memory_forget":
            removed = self._memory.forget(args["memory_id"])
            return json.dumps({"removed": removed})

        else:
            return json.dumps({"error": f"Unknown function: {function_name}"})
