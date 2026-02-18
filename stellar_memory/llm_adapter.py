"""LLM adapter - middleware that integrates memory into LLM conversations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.stellar import StellarMemory
    from stellar_memory.models import SessionInfo

logger = logging.getLogger(__name__)


class MemoryMiddleware:
    """Middleware: before_chat (recall) -> LLM -> after_chat (auto store + feedback)."""

    def __init__(self, memory: StellarMemory, recall_limit: int = 5,
                 auto_store: bool = True, auto_evaluate: bool = True):
        self._memory = memory
        self._recall_limit = recall_limit
        self._auto_store = auto_store
        self._auto_evaluate = auto_evaluate
        self._last_result_ids: list[str] = []

    def before_chat(self, user_message: str) -> str:
        """Recall relevant memories and build context prefix."""
        memories = self._memory.recall(user_message, limit=self._recall_limit)
        self._last_result_ids = [m.id for m in memories]
        if not memories:
            return ""
        lines = ["[Relevant Memories]"]
        for i, mem in enumerate(memories, 1):
            lines.append(f"{i}. {mem.content}")
        return "\n".join(lines)

    def after_chat(self, user_message: str, assistant_response: str) -> None:
        """Auto feedback + optionally store the exchange as a new memory."""
        if self._last_result_ids:
            self._memory.provide_feedback(user_message, self._last_result_ids)
        if not self._auto_store:
            return
        content = f"User: {user_message}\nAssistant: {assistant_response}"
        self._memory.store(
            content=content,
            auto_evaluate=self._auto_evaluate,
            metadata={"source": "conversation"},
        )

    def wrap_messages(self, user_message: str) -> str:
        """Get memory context to prepend to user message."""
        context = self.before_chat(user_message)
        if context:
            return f"{context}\n\n{user_message}"
        return user_message

    def start_session(self) -> SessionInfo:
        return self._memory.start_session()

    def end_session(self) -> SessionInfo | None:
        return self._memory.end_session()


class AnthropicAdapter:
    """Adapter for Anthropic Claude API with memory integration."""

    def __init__(self, middleware: MemoryMiddleware,
                 model: str = "claude-haiku-4-5-20251001",
                 max_tokens: int = 1024):
        self._middleware = middleware
        self._model = model
        self._max_tokens = max_tokens

    def chat(self, user_message: str, system: str | None = None) -> str:
        """Send a message with memory context and store the result."""
        import os
        from anthropic import Anthropic

        enriched = self._middleware.wrap_messages(user_message)

        client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        kwargs: dict = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": [{"role": "user", "content": enriched}],
        }
        if system:
            kwargs["system"] = system

        response = client.messages.create(**kwargs)
        assistant_text = response.content[0].text

        self._middleware.after_chat(user_message, assistant_text)

        return assistant_text
