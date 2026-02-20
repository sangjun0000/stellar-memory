"""Storage layer for Stellar Memory zones."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.models import MemoryItem
    from stellar_memory.config import ZoneConfig, StorageConfig


class ZoneStorage(ABC):
    @abstractmethod
    def store(self, item: MemoryItem) -> None: ...

    @abstractmethod
    def get(self, item_id: str) -> MemoryItem | None: ...

    @abstractmethod
    def remove(self, item_id: str) -> bool: ...

    @abstractmethod
    def update(self, item: MemoryItem) -> None: ...

    @abstractmethod
    def search(self, query: str, limit: int = 5,
               query_embedding: list[float] | None = None) -> list[MemoryItem]: ...

    @abstractmethod
    def get_all(self) -> list[MemoryItem]: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def get_lowest_score_item(self) -> MemoryItem | None: ...


class StorageBackend(ABC):
    """P6: Unified storage backend interface."""

    @abstractmethod
    def store(self, item: MemoryItem) -> None: ...

    @abstractmethod
    def get(self, item_id: str,
            user_id: str | None = None) -> MemoryItem | None: ...

    @abstractmethod
    def remove(self, item_id: str,
               user_id: str | None = None) -> bool: ...

    @abstractmethod
    def update(self, item: MemoryItem) -> None: ...

    @abstractmethod
    def search(self, query: str, limit: int = 5,
               query_embedding: list[float] | None = None,
               zone: int | None = None,
               user_id: str | None = None) -> list[MemoryItem]: ...

    @abstractmethod
    def get_all(self, zone: int | None = None,
                user_id: str | None = None) -> list[MemoryItem]: ...

    @abstractmethod
    def count(self, zone: int | None = None,
              user_id: str | None = None) -> int: ...

    @abstractmethod
    def get_lowest_score_item(self, zone: int) -> MemoryItem | None: ...

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def is_connected(self) -> bool: ...

    def health_check(self) -> bool:
        return self.is_connected()


class StorageFactory:
    def __init__(self, db_path: str = "stellar_memory.db"):
        self._db_path = db_path

    def create(self, zone_config: ZoneConfig) -> ZoneStorage:
        from stellar_memory.storage.in_memory import InMemoryStorage
        if zone_config.zone_id <= 1 or self._db_path == ":memory:":
            return InMemoryStorage()
        try:
            from stellar_memory.storage.sqlite_storage import SqliteStorage
            return SqliteStorage(self._db_path, zone_config.zone_id)
        except Exception:
            return InMemoryStorage()
