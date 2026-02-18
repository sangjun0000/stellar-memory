"""Tests for P7 adapters: LangChain, OpenAI plugin."""

import json
import pytest

from stellar_memory import StellarMemory, StellarConfig
from stellar_memory.adapters.langchain import StellarLangChainMemory
from stellar_memory.adapters.openai_plugin import OpenAIMemoryPlugin, STELLAR_TOOLS


@pytest.fixture
def memory():
    config = StellarConfig(db_path=":memory:")
    return StellarMemory(config)


class TestLangChainAdapter:
    def test_memory_variables(self, memory):
        lc = StellarLangChainMemory(memory)
        assert lc.memory_variables == ["history"]

    def test_custom_memory_key(self, memory):
        lc = StellarLangChainMemory(memory, memory_key="context")
        assert lc.memory_variables == ["context"]

    def test_load_empty(self, memory):
        lc = StellarLangChainMemory(memory)
        result = lc.load_memory_variables({"input": "hello"})
        assert result["history"] == ""

    def test_load_with_memories(self, memory):
        memory.store("Python is my favorite language")
        lc = StellarLangChainMemory(memory)
        result = lc.load_memory_variables({"input": "programming language"})
        assert "Python" in result["history"]

    def test_save_context(self, memory):
        lc = StellarLangChainMemory(memory)
        lc.save_context(
            {"input": "What is Python?"},
            {"output": "Python is a programming language."},
        )
        results = memory.recall("Python")
        assert len(results) >= 1

    def test_clear_noop(self, memory):
        lc = StellarLangChainMemory(memory)
        lc.clear()  # should not raise

    def test_load_empty_input(self, memory):
        lc = StellarLangChainMemory(memory)
        result = lc.load_memory_variables({})
        assert result["history"] == ""


class TestOpenAIPlugin:
    def test_tools_schema(self):
        assert len(STELLAR_TOOLS) == 3
        names = [t["function"]["name"] for t in STELLAR_TOOLS]
        assert "memory_store" in names
        assert "memory_recall" in names
        assert "memory_forget" in names

    def test_get_tools(self, memory):
        plugin = OpenAIMemoryPlugin(memory)
        tools = plugin.get_tools()
        assert tools == STELLAR_TOOLS

    def test_handle_store(self, memory):
        plugin = OpenAIMemoryPlugin(memory)
        result = plugin.handle_call(
            "memory_store",
            json.dumps({"content": "Test store", "importance": 0.7}),
        )
        data = json.loads(result)
        assert "id" in data
        assert "zone" in data

    def test_handle_recall(self, memory):
        memory.store("Python for machine learning")
        plugin = OpenAIMemoryPlugin(memory)
        result = plugin.handle_call(
            "memory_recall",
            json.dumps({"query": "Python", "limit": 5}),
        )
        data = json.loads(result)
        assert isinstance(data, list)

    def test_handle_forget(self, memory):
        item = memory.store("To forget")
        plugin = OpenAIMemoryPlugin(memory)
        result = plugin.handle_call(
            "memory_forget",
            json.dumps({"memory_id": item.id}),
        )
        data = json.loads(result)
        assert data["removed"] is True

    def test_handle_unknown(self, memory):
        plugin = OpenAIMemoryPlugin(memory)
        result = plugin.handle_call("unknown_fn", "{}")
        data = json.loads(result)
        assert "error" in data

    def test_adapters_init_import(self):
        from stellar_memory.adapters import (
            StellarLangChainMemory,
            OpenAIMemoryPlugin,
            STELLAR_TOOLS,
        )
        assert StellarLangChainMemory is not None
        assert OpenAIMemoryPlugin is not None
        assert len(STELLAR_TOOLS) > 0
