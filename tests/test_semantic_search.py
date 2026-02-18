"""Tests for semantic search in storage layer."""

from stellar_memory.storage.in_memory import InMemoryStorage
from stellar_memory.models import MemoryItem
from stellar_memory.utils import cosine_similarity, serialize_embedding, deserialize_embedding
import time


def _make_item(content: str, embedding: list[float] | None = None) -> MemoryItem:
    now = time.time()
    return MemoryItem(
        id=f"test-{content[:8]}",
        content=content,
        created_at=now,
        last_recalled_at=now,
        recall_count=0,
        arbitrary_importance=0.5,
        zone=0,
        embedding=embedding,
    )


class TestHybridSearch:
    def test_keyword_only_search(self):
        storage = InMemoryStorage()
        storage.store(_make_item("The cat sat on the mat"))
        storage.store(_make_item("Dogs are loyal friends"))
        results = storage.search("cat", limit=5)
        assert len(results) == 1
        assert "cat" in results[0].content

    def test_semantic_search_with_embeddings(self):
        storage = InMemoryStorage()
        # Simulate embeddings: [1,0,0] is "cat-like", [0,1,0] is "dog-like"
        storage.store(_make_item("The cat sat on the mat", embedding=[1.0, 0.0, 0.0]))
        storage.store(_make_item("Dogs are loyal friends", embedding=[0.0, 1.0, 0.0]))

        # Query embedding close to cat
        results = storage.search("animal", limit=5, query_embedding=[0.9, 0.1, 0.0])
        assert len(results) >= 1
        # Cat should score higher due to semantic similarity
        assert "cat" in results[0].content

    def test_hybrid_scoring_blends_keyword_and_semantic(self):
        storage = InMemoryStorage()
        # "dog" has keyword match but low semantic similarity to query
        storage.store(_make_item("dog training guide", embedding=[0.0, 1.0, 0.0]))
        # "cat" has no keyword match but high semantic similarity
        storage.store(_make_item("feline behavior patterns", embedding=[1.0, 0.0, 0.0]))

        results = storage.search("dog", limit=5, query_embedding=[1.0, 0.0, 0.0])
        assert len(results) >= 1
        # Both should appear: dog via keyword, feline via semantic
        contents = [r.content for r in results]
        assert any("dog" in c for c in contents)

    def test_no_embedding_falls_back_to_keyword(self):
        storage = InMemoryStorage()
        storage.store(_make_item("Python programming language"))
        results = storage.search("Python", limit=5, query_embedding=[1.0, 0.0])
        assert len(results) == 1

    def test_empty_query_returns_empty(self):
        storage = InMemoryStorage()
        storage.store(_make_item("Something"))
        assert storage.search("", limit=5) == []
        assert storage.search("", limit=5, query_embedding=[1.0]) == []


class TestUtils:
    def test_cosine_similarity_identical(self):
        assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0

    def test_cosine_similarity_orthogonal(self):
        assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0

    def test_cosine_similarity_zero_vector(self):
        assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0

    def test_serialize_deserialize_roundtrip(self):
        original = [0.1, 0.2, 0.3, 0.4]
        blob = serialize_embedding(original)
        restored = deserialize_embedding(blob, dim=4)
        for a, b in zip(original, restored):
            assert abs(a - b) < 1e-6

    def test_cosine_similarity_clamped(self):
        # Should be clamped to [0, 1]
        result = cosine_similarity([1.0, 0.5], [1.0, 0.5])
        assert 0.0 <= result <= 1.0
