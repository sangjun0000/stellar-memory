"""Orbit Manager - manages memory placement and reorbiting across zones."""

from __future__ import annotations

import logging
import time

from stellar_memory.config import ZoneConfig, DEFAULT_ZONES
from stellar_memory.memory_function import MemoryFunction
from stellar_memory.models import MemoryItem, ReorbitResult
from stellar_memory.storage import ZoneStorage, StorageFactory

logger = logging.getLogger(__name__)


class OrbitManager:
    def __init__(self, zones: list[ZoneConfig] | None = None,
                 storage_factory: StorageFactory | None = None):
        zones = zones or DEFAULT_ZONES
        factory = storage_factory or StorageFactory()
        self._zones = {z.zone_id: z for z in zones}
        self._storages: dict[int, ZoneStorage] = {}
        for z in zones:
            self._storages[z.zone_id] = factory.create(z)

    def get_storage(self, zone_id: int) -> ZoneStorage:
        return self._storages[zone_id]

    def place(self, item: MemoryItem, target_zone: int, score: float) -> None:
        target_zone = self._clamp_zone(target_zone)
        item.zone = target_zone
        item.total_score = score

        zone_cfg = self._zones[target_zone]
        storage = self._storages[target_zone]

        if zone_cfg.max_slots is not None and storage.count() >= zone_cfg.max_slots:
            self._evict_lowest(target_zone)

        storage.store(item)

    def move(self, item_id: str, from_zone: int, to_zone: int, score: float) -> bool:
        from_storage = self._storages.get(from_zone)
        if from_storage is None:
            return False
        item = from_storage.get(item_id)
        if item is None:
            return False
        from_storage.remove(item_id)
        self.place(item, to_zone, score)
        return True

    def reorbit_all(self, memory_fn: MemoryFunction, current_time: float) -> ReorbitResult:
        start = time.time()
        all_items: list[MemoryItem] = []
        for storage in self._storages.values():
            all_items.extend(storage.get_all())

        pending_moves: list[tuple[MemoryItem, int, int, float]] = []
        for item in all_items:
            breakdown = memory_fn.calculate(item, current_time)
            item.total_score = breakdown.total
            if breakdown.target_zone != item.zone:
                pending_moves.append((item, item.zone, breakdown.target_zone, breakdown.total))
            else:
                self._storages[item.zone].update(item)

        pending_moves.sort(key=lambda x: x[3], reverse=True)

        moved = 0
        for item, from_z, to_z, score in pending_moves:
            if self.move(item.id, from_z, to_z, score):
                moved += 1

        evicted = 0
        for zone_id in sorted(self._zones.keys()):
            evicted += self._enforce_capacity(zone_id)

        duration = time.time() - start
        return ReorbitResult(
            moved=moved,
            evicted=evicted,
            total_items=len(all_items),
            duration=duration,
        )

    def get_all_items(self, user_id: str | None = None) -> list[MemoryItem]:
        items: list[MemoryItem] = []
        for storage in self._storages.values():
            items.extend(storage.get_all())
        if user_id:
            items = [i for i in items if i.user_id is None or i.user_id == user_id]
        return items

    def get_zone_count(self, zone_id: int) -> int:
        storage = self._storages.get(zone_id)
        return storage.count() if storage else 0

    def find_item(self, item_id: str) -> MemoryItem | None:
        for storage in self._storages.values():
            item = storage.get(item_id)
            if item is not None:
                return item
        return None

    def _evict_lowest(self, zone_id: int) -> list[MemoryItem]:
        storage = self._storages[zone_id]
        evicted: list[MemoryItem] = []
        lowest = storage.get_lowest_score_item()
        if lowest is None:
            return evicted
        storage.remove(lowest.id)
        next_zone = zone_id + 1
        if next_zone in self._storages:
            self.place(lowest, next_zone, lowest.total_score)
        else:
            evicted.append(lowest)
            logger.info(f"Permanently evicted memory {lowest.id}")
        return evicted

    def _enforce_capacity(self, zone_id: int) -> int:
        zone_cfg = self._zones.get(zone_id)
        if zone_cfg is None or zone_cfg.max_slots is None:
            return 0
        storage = self._storages[zone_id]
        evicted = 0
        while storage.count() > zone_cfg.max_slots:
            result = self._evict_lowest(zone_id)
            evicted += len(result)
            if not result and storage.count() > zone_cfg.max_slots:
                break
        return evicted

    def _clamp_zone(self, zone_id: int) -> int:
        valid = sorted(self._zones.keys())
        if zone_id < valid[0]:
            return valid[0]
        if zone_id > valid[-1]:
            return valid[-1]
        return zone_id
