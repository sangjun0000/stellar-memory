"""AI SDK에 기억 능력을 주입하는 미들웨어."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from celestial_engine.auto_memory import AutoMemory
from celestial_engine.models import CelestialItem

if TYPE_CHECKING:
    from celestial_engine import CelestialMemory

logger = logging.getLogger(__name__)


class ContextBuilder:
    """검색된 기억을 시스템 프롬프트용 텍스트로 포매팅."""

    DEFAULT_TEMPLATE = (
        "You have the following memories from previous conversations:\n"
        "{memories}\n"
        "Use these memories naturally when relevant."
    )

    _ZONE_LABELS = ["Core", "Inner", "Outer", "Belt", "Cloud"]

    def __init__(
        self,
        template: str | None = None,
        max_memories: int = 5,
    ) -> None:
        self.template = template or self.DEFAULT_TEMPLATE
        self.max_memories = max_memories

    def build(self, memories: list[CelestialItem]) -> str:
        """기억 리스트를 시스템 프롬프트 문자열로 변환."""
        if not memories:
            return ""
        items = memories[: self.max_memories]
        lines: list[str] = []
        for mem in items:
            label = (
                self._ZONE_LABELS[mem.zone]
                if 0 <= mem.zone <= 4
                else "Unknown"
            )
            lines.append(f"- [{label}] {mem.content}")
        memory_text = "\n".join(lines)
        return self.template.format(memories=memory_text)


class MemoryMiddleware:
    """AI SDK에 기억 능력을 주입하는 미들웨어."""

    def __init__(
        self,
        memory: CelestialMemory,
        auto_memory: AutoMemory | None = None,
        context_builder: ContextBuilder | None = None,
        recall_limit: int = 5,
    ) -> None:
        self.memory = memory
        self.auto_memory = auto_memory or AutoMemory(memory)
        self.context_builder = context_builder or ContextBuilder()
        self.recall_limit = recall_limit

    def recall_context(self, query: str) -> str:
        """쿼리로 기억 검색 후 시스템 프롬프트 텍스트 반환."""
        memories = self.memory.recall(query, limit=self.recall_limit)
        return self.context_builder.build(memories)

    def save_interaction(
        self, user_msg: str, ai_response: str
    ) -> list[CelestialItem]:
        """대화 턴을 분석하여 중요한 사실을 기억에 저장."""
        return self.auto_memory.process_turn(user_msg, ai_response)

    def wrap_openai(self, client) -> OpenAIWrapper:
        """OpenAI 클라이언트를 기억 미들웨어로 래핑."""
        return OpenAIWrapper(client, self)

    def wrap_anthropic(self, client) -> AnthropicWrapper:
        """Anthropic 클라이언트를 기억 미들웨어로 래핑."""
        return AnthropicWrapper(client, self)


# ---------------------------------------------------------------------------
# OpenAI Wrapper
# ---------------------------------------------------------------------------


class _OpenAICompletionsProxy:
    def __init__(self, client, middleware: MemoryMiddleware) -> None:
        self._client = client
        self._middleware = middleware

    def create(self, **kwargs):
        """chat.completions.create()를 가로채서 기억 주입."""
        messages = list(kwargs.get("messages", []))

        # 1. 마지막 user 메시지에서 쿼리 추출
        user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_msg = msg.get("content", "")
                break

        # 2. 기억 검색 -> 시스템 프롬프트 주입
        if user_msg:
            memory_context = self._middleware.recall_context(user_msg)
            if memory_context:
                if messages and messages[0].get("role") == "system":
                    messages[0] = {
                        "role": "system",
                        "content": messages[0]["content"]
                        + "\n\n"
                        + memory_context,
                    }
                else:
                    messages.insert(
                        0, {"role": "system", "content": memory_context}
                    )

        # 3. 원본 API 호출
        kwargs["messages"] = messages
        response = self._client.chat.completions.create(**kwargs)

        # 4. 대화 저장
        if user_msg and response.choices:
            ai_response = response.choices[0].message.content or ""
            try:
                self._middleware.save_interaction(user_msg, ai_response)
            except Exception:
                logger.debug("Failed to save interaction", exc_info=True)

        return response


class _OpenAIChatProxy:
    def __init__(self, client, middleware: MemoryMiddleware) -> None:
        self._client = client
        self._middleware = middleware
        self.completions = _OpenAICompletionsProxy(client, middleware)


class OpenAIWrapper:
    """OpenAI 클라이언트 래퍼 - chat.completions.create() 가로채기."""

    def __init__(self, client, middleware: MemoryMiddleware) -> None:
        try:
            import openai  # noqa: F401
        except ImportError:
            raise ImportError(
                "openai package is required for OpenAI integration. "
                "Install with: pip install stellar-memory[openai]"
            )
        self._client = client
        self._middleware = middleware
        self.chat = _OpenAIChatProxy(client, middleware)


# ---------------------------------------------------------------------------
# Anthropic Wrapper
# ---------------------------------------------------------------------------


class _AnthropicMessagesProxy:
    def __init__(self, client, middleware: MemoryMiddleware) -> None:
        self._client = client
        self._middleware = middleware

    def create(self, **kwargs):
        """messages.create()를 가로채서 기억 주입."""
        messages = list(kwargs.get("messages", []))
        system = kwargs.get("system", "")

        # 1. 마지막 user 메시지에서 쿼리 추출
        user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            user_msg = block.get("text", "")
                            break
                else:
                    user_msg = content
                break

        # 2. 기억 검색 -> system 프롬프트에 주입
        if user_msg:
            memory_context = self._middleware.recall_context(user_msg)
            if memory_context:
                if system:
                    system = system + "\n\n" + memory_context
                else:
                    system = memory_context
                kwargs["system"] = system

        # 3. 원본 API 호출
        kwargs["messages"] = messages
        response = self._client.messages.create(**kwargs)

        # 4. 대화 저장
        if user_msg and response.content:
            ai_text_parts: list[str] = []
            for block in response.content:
                if hasattr(block, "text"):
                    ai_text_parts.append(block.text)
            ai_response = "\n".join(ai_text_parts)
            try:
                self._middleware.save_interaction(user_msg, ai_response)
            except Exception:
                logger.debug("Failed to save interaction", exc_info=True)

        return response


class AnthropicWrapper:
    """Anthropic 클라이언트 래퍼 - messages.create() 가로채기."""

    def __init__(self, client, middleware: MemoryMiddleware) -> None:
        try:
            import anthropic  # noqa: F401
        except ImportError:
            raise ImportError(
                "anthropic package is required for Anthropic integration. "
                "Install with: pip install stellar-memory[llm]"
            )
        self._client = client
        self._middleware = middleware
        self.messages = _AnthropicMessagesProxy(client, middleware)
