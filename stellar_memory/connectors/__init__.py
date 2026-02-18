"""External knowledge connectors for Stellar Memory (P6)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.models import IngestResult

__all__ = [
    "KnowledgeConnector",
    "WebConnector",
    "FileConnector",
    "ApiConnector",
]


class KnowledgeConnector(ABC):
    """Base class for external knowledge ingestion."""

    @abstractmethod
    def ingest(self, source: str, **kwargs) -> IngestResult:
        """Ingest from the given source and return result."""
        ...

    @abstractmethod
    def can_handle(self, source: str) -> bool:
        """Return True if this connector can handle the source."""
        ...


# Lazy imports to avoid requiring optional deps at import time
def WebConnector(*args, **kwargs):  # noqa: N802
    from stellar_memory.connectors.web_connector import WebConnector as _WC
    return _WC(*args, **kwargs)


def FileConnector(*args, **kwargs):  # noqa: N802
    from stellar_memory.connectors.file_connector import FileConnector as _FC
    return _FC(*args, **kwargs)


def ApiConnector(*args, **kwargs):  # noqa: N802
    from stellar_memory.connectors.api_connector import ApiConnector as _AC
    return _AC(*args, **kwargs)
