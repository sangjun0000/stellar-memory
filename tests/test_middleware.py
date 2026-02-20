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
        # Use important content that passes the 0.3 threshold
        mw.after_chat(
            "Remember this critical meeting deadline 2024-03-01!",
            "I'll remember the meeting deadline.",
        )
        results = sm.recall("meeting deadline")
        assert len(results) >= 1

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

    def test_chat_full_loop(self):
        sm = StellarMemory(_make_config())
        sm.store("Python was created by Guido van Rossum", importance=0.9)
        mw = MemoryMiddleware(sm, auto_store=True)

        def mock_llm(system_context: str, user_message: str) -> str:
            return "Python was indeed created by Guido."

        context, response = mw.chat("Python created", mock_llm)
        assert "Relevant Memories" in context
        assert "Guido" in response

    def test_after_chat_skips_trivial(self):
        sm = StellarMemory(_make_config())
        mw = MemoryMiddleware(sm, auto_store=True)
        result = mw.after_chat("ok", "Sure!")
        # Trivial message should not be stored (importance < 0.3)
        assert result is None

    def test_context_includes_zone_names(self):
        sm = StellarMemory(_make_config())
        sm.store("Important fact about space", importance=0.9)
        mw = MemoryMiddleware(sm)
        context = mw.before_chat("space")
        # Should contain zone label like [Core], [Inner], etc.
        assert "[" in context and "]" in context

    def test_create_middleware_on_stellar(self):
        sm = StellarMemory(_make_config())
        mw = sm.create_middleware(max_context=3)
        assert isinstance(mw, MemoryMiddleware)
