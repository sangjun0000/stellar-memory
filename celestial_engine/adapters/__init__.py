"""AI framework adapters for Celestial Memory Engine."""

from __future__ import annotations

__all__ = [
    "LangChainAdapter",
    "OpenAIAdapter",
    "AnthropicAdapter",
]


def __getattr__(name: str):
    if name == "LangChainAdapter":
        from celestial_engine.adapters.langchain import LangChainAdapter
        return LangChainAdapter
    if name == "OpenAIAdapter":
        from celestial_engine.adapters.openai import OpenAIAdapter
        return OpenAIAdapter
    if name == "AnthropicAdapter":
        from celestial_engine.adapters.anthropic import AnthropicAdapter
        return AnthropicAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
