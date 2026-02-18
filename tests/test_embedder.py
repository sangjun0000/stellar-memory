"""Tests for embedder module."""

from stellar_memory.embedder import Embedder, NullEmbedder, create_embedder
from stellar_memory.config import EmbedderConfig


class TestNullEmbedder:
    def test_embed_returns_none(self):
        e = NullEmbedder()
        assert e.embed("hello") is None

    def test_embed_batch_returns_nones(self):
        e = NullEmbedder()
        result = e.embed_batch(["a", "b", "c"])
        assert result == [None, None, None]

    def test_embed_batch_empty(self):
        e = NullEmbedder()
        assert e.embed_batch([]) == []


class TestCreateEmbedder:
    def test_disabled_returns_null(self):
        cfg = EmbedderConfig(enabled=False)
        e = create_embedder(cfg)
        assert isinstance(e, NullEmbedder)

    def test_default_config_graceful(self):
        """Without sentence-transformers installed, should return NullEmbedder."""
        cfg = EmbedderConfig(enabled=True)
        e = create_embedder(cfg)
        # Either Embedder (if installed) or NullEmbedder (if not)
        assert hasattr(e, "embed")
        assert hasattr(e, "embed_batch")

    def test_none_config_uses_default(self):
        e = create_embedder(None)
        assert hasattr(e, "embed")
