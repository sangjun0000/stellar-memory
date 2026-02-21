"""Tests for Plugin system (v3.0 SDK)."""

import pytest

from stellar_memory.builder import StellarBuilder, Preset
from stellar_memory.plugin import MemoryPlugin


def _make_memory():
    """Helper to create a minimal in-memory StellarMemory."""
    return StellarBuilder(Preset.MINIMAL).with_memory().build()


class TestMemoryPluginBase:
    """Base class default methods are no-ops."""

    def test_default_on_store_returns_item(self):
        from stellar_memory.models import MemoryItem
        plugin = MemoryPlugin()
        item = MemoryItem.create("test", 0.5)
        assert plugin.on_store(item) is item

    def test_default_on_pre_recall_returns_query(self):
        plugin = MemoryPlugin()
        assert plugin.on_pre_recall("hello") == "hello"

    def test_default_on_recall_returns_results(self):
        plugin = MemoryPlugin()
        results = [1, 2, 3]
        assert plugin.on_recall("q", results) is results

    def test_default_on_decay_returns_score(self):
        plugin = MemoryPlugin()
        assert plugin.on_decay(None, 0.42) == 0.42

    def test_default_on_forget_returns_true(self):
        plugin = MemoryPlugin()
        assert plugin.on_forget("abc") is True


class TestPluginOnStore:
    def test_on_store_modifies_item(self):
        class TagPlugin(MemoryPlugin):
            name = "tagger"
            def on_store(self, item):
                item.metadata = item.metadata or {}
                item.metadata["tagged"] = True
                return item

        memory = _make_memory()
        memory.use(TagPlugin())
        item = memory.store("hello world", importance=0.5)
        assert item.metadata.get("tagged") is True
        memory.stop()


class TestPluginOnRecall:
    def test_on_recall_filters_results(self):
        class FilterPlugin(MemoryPlugin):
            name = "filter"
            def on_recall(self, query, results):
                return [r for r in results if "important" in r.content]

        memory = _make_memory()
        memory.use(FilterPlugin())
        memory.store("important data", importance=0.9)
        memory.store("trivial stuff", importance=0.9)
        results = memory.recall("data", limit=10)
        assert all("important" in r.content for r in results)
        memory.stop()


class TestPluginOnForget:
    def test_on_forget_cancels_deletion(self):
        class ProtectPlugin(MemoryPlugin):
            name = "protector"
            protected_ids = set()
            def on_forget(self, memory_id):
                return memory_id not in self.protected_ids

        plugin = ProtectPlugin()
        memory = _make_memory()
        memory.use(plugin)
        item = memory.store("protected memory", importance=0.9)
        plugin.protected_ids.add(item.id)

        result = memory.forget(item.id)
        assert result is False  # Deletion cancelled
        assert memory.get(item.id) is not None  # Still exists
        memory.stop()


class TestPluginOnInit:
    def test_on_init_receives_memory_ref(self):
        class InitPlugin(MemoryPlugin):
            name = "init-checker"
            received_memory = None
            def on_init(self, memory):
                InitPlugin.received_memory = memory

        memory = _make_memory()
        memory.use(InitPlugin())
        assert InitPlugin.received_memory is memory
        memory.stop()


class TestPluginChainOrder:
    def test_multiple_plugins_called_in_order(self):
        call_order = []

        class Plugin1(MemoryPlugin):
            name = "first"
            def on_store(self, item):
                call_order.append("first")
                return item

        class Plugin2(MemoryPlugin):
            name = "second"
            def on_store(self, item):
                call_order.append("second")
                return item

        memory = _make_memory()
        memory.use(Plugin1())
        memory.use(Plugin2())
        memory.store("test", importance=0.5)
        assert call_order == ["first", "second"]
        memory.stop()


class TestPluginOnShutdown:
    def test_shutdown_called_on_stop(self):
        class ShutdownPlugin(MemoryPlugin):
            name = "shutdown"
            shutdown_called = False
            def on_shutdown(self):
                ShutdownPlugin.shutdown_called = True

        memory = _make_memory()
        memory.use(ShutdownPlugin())
        memory.stop()
        assert ShutdownPlugin.shutdown_called


class TestPluginErrorHandling:
    def test_failing_plugin_does_not_crash(self):
        class BrokenPlugin(MemoryPlugin):
            name = "broken"
            def on_store(self, item):
                raise RuntimeError("Plugin crashed!")

        memory = _make_memory()
        memory.use(BrokenPlugin())
        # Should not raise
        item = memory.store("still works", importance=0.5)
        assert item is not None
        memory.stop()
