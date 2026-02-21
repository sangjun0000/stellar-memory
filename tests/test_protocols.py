"""Tests for Protocol interfaces (v3.0 SDK)."""

import pytest

from stellar_memory.protocols import (
    MemoryStore,
    StorageBackendProtocol,
    EmbedderProvider,
    LLMProvider,
    ImportanceEvaluator,
    EventHook,
)


class TestProtocolsRuntimeCheckable:
    """All protocols must be @runtime_checkable."""

    def test_memory_store_checkable(self):
        assert hasattr(MemoryStore, '__protocol_attrs__') or hasattr(MemoryStore, '_is_runtime_protocol')

    def test_storage_backend_checkable(self):
        assert hasattr(StorageBackendProtocol, '__protocol_attrs__') or hasattr(StorageBackendProtocol, '_is_runtime_protocol')

    def test_embedder_provider_checkable(self):
        assert hasattr(EmbedderProvider, '__protocol_attrs__') or hasattr(EmbedderProvider, '_is_runtime_protocol')

    def test_llm_provider_checkable(self):
        assert hasattr(LLMProvider, '__protocol_attrs__') or hasattr(LLMProvider, '_is_runtime_protocol')


class TestProtocolConformance:
    """Test that existing implementations conform to protocols."""

    def test_sqlite_storage_conforms_to_protocol(self):
        """SqliteStorage should structurally match StorageBackendProtocol."""
        from stellar_memory.storage.sqlite_storage import SqliteStorage
        storage = SqliteStorage(":memory:", 0)
        assert isinstance(storage, StorageBackendProtocol)

    def test_in_memory_storage_conforms(self):
        from stellar_memory.storage.in_memory import InMemoryStorage
        storage = InMemoryStorage()
        assert isinstance(storage, StorageBackendProtocol)

    def test_custom_storage_matches(self):
        """A custom class with matching methods should pass isinstance."""
        class MyStorage:
            def store(self, item): pass
            def get(self, item_id): return None
            def get_all(self): return []
            def update(self, item): pass
            def remove(self, item_id): return True
            def search(self, query, limit=5, query_embedding=None): return []
            def count(self): return 0

        assert isinstance(MyStorage(), StorageBackendProtocol)

    def test_custom_embedder_matches(self):
        class MyEmbedder:
            def embed(self, text): return [0.1, 0.2]
            def embed_batch(self, texts): return [[0.1]] * len(texts)

        assert isinstance(MyEmbedder(), EmbedderProvider)

    def test_custom_llm_matches(self):
        class MyLLM:
            def complete(self, prompt, *, max_tokens=256): return "ok"

        assert isinstance(MyLLM(), LLMProvider)

    def test_custom_evaluator_matches(self):
        class MyEvaluator:
            def evaluate(self, content, metadata=None): return 0.5

        assert isinstance(MyEvaluator(), ImportanceEvaluator)


class TestProtocolReExports:
    """Protocols should be re-exported from providers/__init__.py."""

    def test_embedder_provider_from_providers(self):
        from stellar_memory.providers import EmbedderProvider as EP
        assert EP is EmbedderProvider

    def test_llm_provider_from_providers(self):
        from stellar_memory.providers import LLMProvider as LP
        assert LP is LLMProvider
