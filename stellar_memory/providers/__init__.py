"""Provider registry for LLM and Embedder backends."""

from __future__ import annotations

import logging
from typing import Callable, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    def complete(self, prompt: str, max_tokens: int = 256) -> str: ...


@runtime_checkable
class EmbedderProvider(Protocol):
    """Protocol for embedding providers."""

    def embed(self, text: str) -> list[float]: ...
    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class NullLLMProvider:
    """Fallback LLM provider that raises on use."""

    def complete(self, prompt: str, max_tokens: int = 256) -> str:
        raise RuntimeError("No LLM provider available")


class NullEmbedderProvider:
    """Fallback embedder provider that returns None."""

    def embed(self, text: str) -> None:
        return None

    def embed_batch(self, texts: list[str]) -> list[None]:
        return [None] * len(texts)


class ProviderRegistry:
    """Registry for LLM and Embedder provider factories."""

    _llm_factories: dict[str, Callable] = {}
    _embedder_factories: dict[str, Callable] = {}

    @classmethod
    def register_llm(cls, name: str, factory: Callable) -> None:
        """Register an LLM provider factory."""
        cls._llm_factories[name] = factory

    @classmethod
    def register_embedder(cls, name: str, factory: Callable) -> None:
        """Register an embedder provider factory."""
        cls._embedder_factories[name] = factory

    @classmethod
    def create_llm(cls, config) -> LLMProvider:
        """Create an LLM provider from config."""
        factory = cls._llm_factories.get(config.provider)
        if factory is None:
            raise ValueError(f"Unknown LLM provider: {config.provider}. "
                             f"Available: {list(cls._llm_factories.keys())}")
        return factory(config)

    @classmethod
    def create_embedder(cls, config) -> EmbedderProvider:
        """Create an embedder provider from config."""
        factory = cls._embedder_factories.get(config.provider)
        if factory is None:
            raise ValueError(f"Unknown embedder provider: {config.provider}. "
                             f"Available: {list(cls._embedder_factories.keys())}")
        return factory(config)

    @classmethod
    def available_llm_providers(cls) -> list[str]:
        return list(cls._llm_factories.keys())

    @classmethod
    def available_embedder_providers(cls) -> list[str]:
        return list(cls._embedder_factories.keys())


# --- Built-in provider registrations ---

def _create_anthropic_llm(config):
    """Factory for Anthropic LLM provider."""
    import os
    api_key = os.environ.get(config.api_key_env, "")
    if not api_key:
        raise RuntimeError(f"API key not found: {config.api_key_env}")
    from anthropic import Anthropic

    class _AnthropicLLM:
        def __init__(self, cfg):
            self._client = Anthropic(api_key=api_key)
            self._model = cfg.model
        def complete(self, prompt: str, max_tokens: int = 256) -> str:
            response = self._client.messages.create(
                model=self._model, max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

    return _AnthropicLLM(config)


def _try_register_defaults():
    """Register built-in providers with graceful degradation."""
    # Anthropic LLM
    try:
        import anthropic  # noqa: F401
        ProviderRegistry.register_llm("anthropic", _create_anthropic_llm)
    except ImportError:
        pass

    # OpenAI
    try:
        from stellar_memory.providers.openai_provider import (
            create_openai_llm, create_openai_embedder,
        )
        ProviderRegistry.register_llm("openai", create_openai_llm)
        ProviderRegistry.register_embedder("openai", create_openai_embedder)
    except ImportError:
        pass

    # Ollama
    try:
        from stellar_memory.providers.ollama_provider import (
            create_ollama_llm, create_ollama_embedder,
        )
        ProviderRegistry.register_llm("ollama", create_ollama_llm)
        ProviderRegistry.register_embedder("ollama", create_ollama_embedder)
    except Exception:
        pass


_try_register_defaults()
