"""Tests for P5-F1: Multi-Provider LLM/Embedder support."""

from __future__ import annotations

import pytest

from stellar_memory.providers import (
    ProviderRegistry, LLMProvider, EmbedderProvider,
    NullLLMProvider, NullEmbedderProvider,
)
from stellar_memory.config import LLMConfig, EmbedderConfig


# --- Protocol / Null Provider Tests ---

class TestNullProviders:
    def test_null_llm_raises(self):
        llm = NullLLMProvider()
        with pytest.raises(RuntimeError, match="No LLM provider"):
            llm.complete("hello")

    def test_null_embedder_returns_none(self):
        emb = NullEmbedderProvider()
        assert emb.embed("hello") is None

    def test_null_embedder_batch(self):
        emb = NullEmbedderProvider()
        result = emb.embed_batch(["a", "b", "c"])
        assert len(result) == 3
        assert all(r is None for r in result)


# --- Registry Tests ---

class _MockLLM:
    def complete(self, prompt: str, max_tokens: int = 256) -> str:
        return f"mock-{prompt[:10]}"


class _MockEmbedder:
    def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3]] * len(texts)


class TestProviderRegistry:
    def setup_method(self):
        # Save and clear registry state
        self._orig_llm = dict(ProviderRegistry._llm_factories)
        self._orig_emb = dict(ProviderRegistry._embedder_factories)

    def teardown_method(self):
        # Restore registry state
        ProviderRegistry._llm_factories = self._orig_llm
        ProviderRegistry._embedder_factories = self._orig_emb

    def test_register_and_create_llm(self):
        ProviderRegistry.register_llm("mock", lambda cfg: _MockLLM())
        llm = ProviderRegistry.create_llm(LLMConfig(provider="mock"))
        assert isinstance(llm, _MockLLM)
        result = llm.complete("test prompt")
        assert result == "mock-test promp"

    def test_register_and_create_embedder(self):
        ProviderRegistry.register_embedder("mock", lambda cfg: _MockEmbedder())
        emb = ProviderRegistry.create_embedder(EmbedderConfig(provider="mock"))
        assert isinstance(emb, _MockEmbedder)
        vec = emb.embed("test")
        assert len(vec) == 3

    def test_unknown_llm_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            ProviderRegistry.create_llm(LLMConfig(provider="nonexistent_xyz"))

    def test_unknown_embedder_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown embedder provider"):
            ProviderRegistry.create_embedder(EmbedderConfig(provider="nonexistent_xyz"))

    def test_available_providers(self):
        ProviderRegistry.register_llm("test_a", lambda cfg: _MockLLM())
        ProviderRegistry.register_llm("test_b", lambda cfg: _MockLLM())
        providers = ProviderRegistry.available_llm_providers()
        assert "test_a" in providers
        assert "test_b" in providers

    def test_available_embedder_providers(self):
        ProviderRegistry.register_embedder("test_e", lambda cfg: _MockEmbedder())
        providers = ProviderRegistry.available_embedder_providers()
        assert "test_e" in providers


# --- Protocol conformance ---

class TestProtocolConformance:
    def test_mock_llm_implements_protocol(self):
        assert isinstance(_MockLLM(), LLMProvider)

    def test_mock_embedder_implements_protocol(self):
        assert isinstance(_MockEmbedder(), EmbedderProvider)

    def test_null_llm_implements_protocol(self):
        assert isinstance(NullLLMProvider(), LLMProvider)

    def test_null_embedder_implements_protocol(self):
        assert isinstance(NullEmbedderProvider(), EmbedderProvider)


# --- Factory override test ---

class TestFactoryOverride:
    def setup_method(self):
        self._orig_llm = dict(ProviderRegistry._llm_factories)

    def teardown_method(self):
        ProviderRegistry._llm_factories = self._orig_llm

    def test_override_existing_provider(self):
        ProviderRegistry.register_llm("override_test", lambda cfg: _MockLLM())
        llm1 = ProviderRegistry.create_llm(LLMConfig(provider="override_test"))
        assert llm1.complete("x") == "mock-x"

        class _CustomLLM:
            def complete(self, prompt: str, max_tokens: int = 256) -> str:
                return "custom"

        ProviderRegistry.register_llm("override_test", lambda cfg: _CustomLLM())
        llm2 = ProviderRegistry.create_llm(LLMConfig(provider="override_test"))
        assert llm2.complete("x") == "custom"
