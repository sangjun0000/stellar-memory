"""Internal plugin manager for dispatching lifecycle hooks."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.models import MemoryItem
    from stellar_memory.plugin import MemoryPlugin
    from stellar_memory.stellar import StellarMemory

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages registered plugins and dispatches hooks."""

    def __init__(self):
        self._plugins: list[MemoryPlugin] = []

    @property
    def plugins(self) -> list[MemoryPlugin]:
        return list(self._plugins)

    def register(self, plugin: MemoryPlugin, memory: StellarMemory) -> None:
        """Register a plugin and call on_init."""
        self._plugins.append(plugin)
        try:
            plugin.on_init(memory)
        except Exception:
            logger.warning("Plugin %s.on_init failed", plugin.name, exc_info=True)

    def dispatch_store(self, item: MemoryItem) -> MemoryItem:
        """Chain on_store through all plugins."""
        for plugin in self._plugins:
            try:
                item = plugin.on_store(item)
            except Exception:
                logger.warning("Plugin %s.on_store failed", plugin.name, exc_info=True)
        return item

    def dispatch_pre_recall(self, query: str, **kwargs) -> str:
        """Chain on_pre_recall through all plugins."""
        for plugin in self._plugins:
            try:
                query = plugin.on_pre_recall(query, **kwargs)
            except Exception:
                logger.warning("Plugin %s.on_pre_recall failed", plugin.name, exc_info=True)
        return query

    def dispatch_recall(self, query: str,
                        results: list[MemoryItem]) -> list[MemoryItem]:
        """Chain on_recall through all plugins."""
        for plugin in self._plugins:
            try:
                results = plugin.on_recall(query, results)
            except Exception:
                logger.warning("Plugin %s.on_recall failed", plugin.name, exc_info=True)
        return results

    def dispatch_decay(self, item: MemoryItem, score: float) -> float:
        """Chain on_decay through all plugins."""
        for plugin in self._plugins:
            try:
                score = plugin.on_decay(item, score)
            except Exception:
                logger.warning("Plugin %s.on_decay failed", plugin.name, exc_info=True)
        return score

    def dispatch_reorbit(self, moves: list[tuple[str, int, int]]) -> None:
        """Notify all plugins of reorbit."""
        for plugin in self._plugins:
            try:
                plugin.on_reorbit(moves)
            except Exception:
                logger.warning("Plugin %s.on_reorbit failed", plugin.name, exc_info=True)

    def dispatch_forget(self, memory_id: str) -> bool:
        """Check all plugins allow forget. Any False cancels."""
        for plugin in self._plugins:
            try:
                if not plugin.on_forget(memory_id):
                    return False
            except Exception:
                logger.warning("Plugin %s.on_forget failed", plugin.name, exc_info=True)
        return True

    def dispatch_consolidate(self, merged: MemoryItem,
                             sources: list[MemoryItem]) -> MemoryItem:
        """Chain on_consolidate through all plugins."""
        for plugin in self._plugins:
            try:
                merged = plugin.on_consolidate(merged, sources)
            except Exception:
                logger.warning("Plugin %s.on_consolidate failed", plugin.name, exc_info=True)
        return merged

    def shutdown(self) -> None:
        """Call on_shutdown for all plugins."""
        for plugin in self._plugins:
            try:
                plugin.on_shutdown()
            except Exception:
                logger.warning("Plugin %s.on_shutdown failed", plugin.name, exc_info=True)
