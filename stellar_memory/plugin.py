"""MemoryPlugin - Base class for extending StellarMemory.

Override any hook method to intercept memory lifecycle events.
All hooks are optional - only override what you need.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.models import MemoryItem
    from stellar_memory.stellar import StellarMemory


class MemoryPlugin:
    """Base class for memory plugins.

    Example::

        class MyPlugin(MemoryPlugin):
            name = "my-plugin"

            def on_store(self, item):
                item.metadata["source"] = "my-app"
                return item

        memory = StellarBuilder().with_plugin(MyPlugin()).build()
    """

    name: str = "unnamed-plugin"

    def on_init(self, memory: StellarMemory) -> None:
        """Called when plugin is registered via memory.use()."""

    def on_store(self, item: MemoryItem) -> MemoryItem:
        """Called after a memory is stored. Return modified item."""
        return item

    def on_pre_recall(self, query: str, **kwargs) -> str:
        """Called before recall. Return modified query."""
        return query

    def on_recall(self, query: str, results: list[MemoryItem]) -> list[MemoryItem]:
        """Called after recall. Return modified results."""
        return results

    def on_decay(self, item: MemoryItem, new_score: float) -> float:
        """Called during decay calculation. Return adjusted score."""
        return new_score

    def on_reorbit(self, moves: list[tuple[str, int, int]]) -> None:
        """Called after reorbit. moves = [(item_id, old_zone, new_zone)]."""

    def on_forget(self, memory_id: str) -> bool:
        """Called before forget. Return False to cancel deletion."""
        return True

    def on_consolidate(self, merged_item: MemoryItem,
                       source_items: list[MemoryItem]) -> MemoryItem:
        """Called after consolidation. Return modified merged item."""
        return merged_item

    def on_shutdown(self) -> None:
        """Called when memory.stop() is called."""
