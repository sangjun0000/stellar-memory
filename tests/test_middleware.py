"""Tests for LLM adapter and middleware module."""

from stellar_memory.llm_adapter import MemoryMiddleware
from stellar_memory.stellar import StellarMemory
from stellar_memory.config import StellarConfig, MemoryFunctionConfig, ZoneConfig, EmbedderConfig


def _make_config() -> StellarConfig:
    return StellarConfig(
        memory_function=MemoryFunctionConfig(decay_alpha=0.001),
        zones=[
            ZoneConfig(0, "core", max_slots=5, importance_min=0.8),
            ZoneConfig(1, "inner", max_slots=10, importance_min=0.5, importance_max=0.8),
            ZoneConfig(2, "outer", max_slots=100, importance_min=0.2, importance_max=0.5),
            ZoneConfig(3, "belt", max_slots=None, importance_min=0.0, importance_max=0.2),
        ],
        db_path=":memory:",
        auto_start_scheduler=False,
        embedder=EmbedderConfig(enabled=False),
    )


class TestMemoryMiddleware:
    def test_before_chat_no_memories(self):
        sm = StellarMemory(_make_config())
        mw = MemoryMiddleware(sm)
        context = mw.before_chat("Hello world")
        assert context == ""

    def test_before_chat_with_memories(self):
        sm = StellarMemory(_make_config())
        sm.store("Python is a programming language", importance=0.9)
        mw = MemoryMiddleware(sm)
        context = mw.before_chat("Python")
        assert "Relevant Memories" in context
        assert "Python" in context

    def test_after_chat_stores_conversation(self):
        sm = StellarMemory(_make_config())
        mw = MemoryMiddleware(sm, auto_store=True, auto_evaluate=False)
        mw.after_chat("What is Python?", "Python is a programming language.")
        # Should now find the conversation in memory
        results = sm.recall("Python")
        assert len(results) >= 1
        assert "Python" in results[0].content

    def test_after_chat_disabled(self):
        sm = StellarMemory(_make_config())
        mw = MemoryMiddleware(sm, auto_store=False)
        mw.after_chat("question", "answer")
        results = sm.recall("question")
        assert len(results) == 0

    def test_wrap_messages_with_context(self):
        sm = StellarMemory(_make_config())
        sm.store("Important fact about cats", importance=0.9)
        mw = MemoryMiddleware(sm)
        enriched = mw.wrap_messages("Tell me about cats")
        assert "Relevant Memories" in enriched
        assert "Tell me about cats" in enriched

    def test_wrap_messages_no_context(self):
        sm = StellarMemory(_make_config())
        mw = MemoryMiddleware(sm)
        enriched = mw.wrap_messages("Hello")
        assert enriched == "Hello"

    def test_recall_limit_respected(self):
        sm = StellarMemory(_make_config())
        for i in range(10):
            sm.store(f"Memory about topic number {i}", importance=0.9)
        mw = MemoryMiddleware(sm, recall_limit=3)
        context = mw.before_chat("topic")
        lines = [l for l in context.split("\n") if l.strip().startswith(("1.", "2.", "3.", "4."))]
        assert len(lines) <= 3
