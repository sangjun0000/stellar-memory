"""Zone Manager - handles memory placement, movement, eviction, and search."""

from __future__ import annotations

import logging

from celestial_engine.models import CelestialItem, ZoneConfig, DEFAULT_ZONES
from celestial_engine.storage import ZoneStorage
from celestial_engine.storage.memory import InMemoryStorage
from celestial_engine.storage.sqlite import SqliteStorage

logger = logging.getLogger(__name__)


class ZoneManager:
    """Manages 5 orbital zones: Core, Inner, Outer, Belt, Cloud."""

    def __init__(
        self,
        zones: list[ZoneConfig] | None = None,
        db_path: str = "celestial_memory.db",
    ) -> None:
        zone_list = zones or DEFAULT_ZONES
        self._zones: dict[int, ZoneConfig] = {z.zone_id: z for z in zone_list}
        self._storages: dict[int, ZoneStorage] = {}
        for z in zone_list:
            if z.zone_id <= 1 or db_path == ":memory:":
                self._storages[z.zone_id] = InMemoryStorage()
            else:
                self._storages[z.zone_id] = SqliteStorage(db_path, z.zone_id)

    def place(self, item: CelestialItem, target_zone: int, score: float) -> None:
        """Place item in target zone. Evicts lowest-score item if at capacity."""
        target_zone = self._clamp_zone(target_zone)
        item.zone = target_zone
        item.total_score = score

        zone_cfg = self._zones[target_zone]
        storage = self._storages[target_zone]

        if zone_cfg.max_slots is not None and storage.count() >= zone_cfg.max_slots:
            self._evict_lowest(target_zone)

        storage.store(item)

    def move(self, item_id: str, from_zone: int, to_zone: int, score: float) -> bool:
        """Move item from one zone to another."""
        from_storage = self._storages.get(from_zone)
        if from_storage is None:
            return False
        item = from_storage.get(item_id)
        if item is None:
            return False
        from_storage.remove(item_id)
        self.place(item, to_zone, score)
        return True

    def get_all_items(self) -> list[CelestialItem]:
        """Return all items across all zones."""
        items: list[CelestialItem] = []
        for storage in self._storages.values():
            items.extend(storage.get_all())
        return items

    def search(
        self,
        query: str,
        limit: int = 5,
        query_embedding: list[float] | None = None,
    ) -> list[CelestialItem]:
        """Search across zones in order (0->4). Stops at limit."""
        results: list[CelestialItem] = []
        for zone_id in sorted(self._storages.keys()):
            if len(results) >= limit:
                break
            storage = self._storages[zone_id]
            remaining = limit - len(results)
            found = storage.search(query, remaining, query_embedding)
            results.extend(found)
        return results[:limit]

    def forget_stale(self, max_age_seconds: float, current_time: float) -> int:
        """Delete items in Cloud zone older than max_age_seconds."""
        cloud = self._storages.get(4)
        if cloud is None:
            return 0
        forgotten = 0
        for item in cloud.get_all():
            if current_time - item.last_recalled_at > max_age_seconds:
                cloud.remove(item.id)
                forgotten += 1
        return forgotten

    def enforce_capacity(self) -> int:
        """Enforce capacity limits on all zones. Returns eviction count."""
        evicted = 0
        for zone_id in sorted(self._zones.keys()):
            zone_cfg = self._zones[zone_id]
            if zone_cfg.max_slots is None:
                continue
            storage = self._storages[zone_id]
            while storage.count() > zone_cfg.max_slots:
                before = storage.count()
                self._evict_lowest(zone_id)
                if storage.count() >= before:
                    break
                evicted += 1
        return evicted

    def stats(self) -> dict[int, tuple[int, int | None]]:
        """Return (count, capacity) for each zone."""
        return {
            zid: (self._storages[zid].count(), self._zones[zid].max_slots)
            for zid in sorted(self._zones.keys())
        }

    def find_item(self, item_id: str) -> CelestialItem | None:
        """Find an item across all zones."""
        for storage in self._storages.values():
            item = storage.get(item_id)
            if item is not None:
                return item
        return None

    def _evict_lowest(self, zone_id: int) -> None:
        storage = self._storages[zone_id]
        lowest = storage.get_lowest_score_item()
        if lowest is None:
            return
        storage.remove(lowest.id)
        next_zone = zone_id + 1
        if next_zone in self._storages:
            self.place(lowest, next_zone, lowest.total_score)
        else:
            logger.info("Permanently evicted memory %s", lowest.id)

    def _clamp_zone(self, zone_id: int) -> int:
        valid = sorted(self._zones.keys())
        if zone_id < valid[0]:
            return valid[0]
        if zone_id > valid[-1]:
            return valid[-1]
        return zone_id
