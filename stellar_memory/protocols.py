"""Protocol interfaces for Stellar Memory SDK v3.0.

Derivative products should depend on these stable interfaces
rather than concrete implementations.
"""

from __future__ import annotations

from typing import Any, Callable, Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.models import MemoryItem, MemoryStats


@runtime_checkable
class MemoryStore(Protocol):
    """Core memory interface - derivative products depend on this."""

    def store(self, content: str, *, importance: float = 0.5,
              metadata: dict[str, Any] | None = None) -> str:
        """Store a memory. Returns memory ID."""
        ...

    def recall(self, query: str, *, limit: int = 5,
               min_score: float = 0.0) -> list[MemoryItem]:
        """Recall relevant memories."""
        ...

    def get(self, memory_id: str) -> MemoryItem | None:
        """Get memory by ID."""
        ...

    def forget(self, memory_id: str) -> bool:
        """Delete a memory."""
        ...

    def stats(self) -> MemoryStats:
        """Get memory statistics."""
        ...


@runtime_checkable
class StorageBackendProtocol(Protocol):
    """Storage extension interface (Protocol version).

    Complements the existing ZoneStorage ABC for structural subtyping.
    """

    def store(self, item: MemoryItem) -> None: ...
    def get(self, item_id: str) -> MemoryItem | None: ...
    def get_all(self) -> list[MemoryItem]: ...
    def update(self, item: MemoryItem) -> None: ...
    def remove(self, item_id: str) -> bool: ...
    def search(self, query: str, limit: int = 5,
               query_embedding: list[float] | None = None) -> list[MemoryItem]: ...
    def count(self) -> int: ...


@runtime_checkable
class EmbedderProvider(Protocol):
    """Embedding extension interface."""

    def embed(self, text: str) -> list[float] | None: ...
    def embed_batch(self, texts: list[str]) -> list[list[float] | None]: ...


@runtime_checkable
class LLMProvider(Protocol):
    """LLM provider interface."""

    def complete(self, prompt: str, *, max_tokens: int = 256) -> str: ...


@runtime_checkable
class ImportanceEvaluator(Protocol):
    """Importance evaluation extension interface."""

    def evaluate(self, content: str,
                 metadata: dict[str, Any] | None = None) -> float: ...


@runtime_checkable
class EventHook(Protocol):
    """Event hook for lifecycle integration."""

    def on_event(self, event_type: str,
                 data: dict[str, Any]) -> dict[str, Any] | None:
        """Handle an event. Return modified data or None."""
        ...
