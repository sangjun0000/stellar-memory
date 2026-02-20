"""Storage layer for Celestial Memory Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from celestial_engine.models import CelestialItem


class ZoneStorage(ABC):
    """Abstract storage interface for a single zone."""

    @abstractmethod
    def store(self, item: CelestialItem) -> None: ...

    @abstractmethod
    def get(self, item_id: str) -> CelestialItem | None: ...

    @abstractmethod
    def remove(self, item_id: str) -> bool: ...

    @abstractmethod
    def update(self, item: CelestialItem) -> None: ...

    @abstractmethod
    def search(
        self,
        query: str,
        limit: int = 5,
        query_embedding: list[float] | None = None,
    ) -> list[CelestialItem]: ...

    @abstractmethod
    def get_all(self) -> list[CelestialItem]: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def get_lowest_score_item(self) -> CelestialItem | None: ...
