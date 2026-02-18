"""Text embedding for semantic search and context relevance."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.config import EmbedderConfig

logger = logging.getLogger(__name__)


class Embedder:
    """Generate text embeddings using sentence-transformers."""

    def __init__(self, config: EmbedderConfig | None = None):
        from stellar_memory.config import EmbedderConfig as _EC
        self._config = config or _EC()
        self._model = None

    def _ensure_model(self) -> None:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._config.model_name)

    @lru_cache(maxsize=128)
    def _cached_embed(self, text: str) -> tuple[float, ...]:
        vector = self._model.encode(text, normalize_embeddings=True)
        return tuple(vector.tolist())

    def embed(self, text: str) -> list[float]:
        """Embed a single text into a vector."""
        self._ensure_model()
        return list(self._cached_embed(text))

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts in a batch."""
        self._ensure_model()
        vectors = self._model.encode(
            texts,
            batch_size=self._config.batch_size,
            normalize_embeddings=True,
        )
        return [v.tolist() for v in vectors]


class NullEmbedder:
    """Fallback when sentence-transformers is not installed."""

    def embed(self, text: str) -> None:
        return None

    def embed_batch(self, texts: list[str]) -> list[None]:
        return [None] * len(texts)


def create_embedder(config: EmbedderConfig | None = None) -> Embedder | NullEmbedder:
    """Create an embedder with graceful degradation."""
    from stellar_memory.config import EmbedderConfig as _EC
    cfg = config or _EC()
    if not cfg.enabled:
        return NullEmbedder()
    if cfg.provider == "sentence-transformers":
        try:
            import sentence_transformers  # noqa: F401
            return Embedder(cfg)
        except ImportError:
            logger.warning("sentence-transformers not installed, using NullEmbedder")
            return NullEmbedder()
    else:
        try:
            from stellar_memory.providers import ProviderRegistry
            return ProviderRegistry.create_embedder(cfg)
        except Exception:
            logger.warning("Embedder provider %s not available, using NullEmbedder",
                           cfg.provider)
            return NullEmbedder()
