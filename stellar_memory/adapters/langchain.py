"""LangChain Memory interface adapter for Stellar Memory."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.stellar import StellarMemory


class StellarLangChainMemory:
    """LangChain BaseMemory compatible adapter.

    Usage::

        from stellar_memory import StellarMemory
        from stellar_memory.adapters.langchain import StellarLangChainMemory

        memory = StellarMemory()
        lc_memory = StellarLangChainMemory(memory)
        # Use with LangChain ConversationChain
    """

    memory_key: str = "history"
    input_key: str = "input"
    output_key: str = "output"

    def __init__(self, stellar_memory: StellarMemory,
                 recall_limit: int = 5,
                 memory_key: str = "history"):
        self._memory = stellar_memory
        self._recall_limit = recall_limit
        self.memory_key = memory_key

    @property
    def memory_variables(self) -> list[str]:
        return [self.memory_key]

    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, str]:
        """Recall relevant memories based on input."""
        query = inputs.get(self.input_key, "")
        if not query:
            return {self.memory_key: ""}

        results = self._memory.recall(str(query), limit=self._recall_limit)
        if not results:
            return {self.memory_key: ""}

        context = "\n".join(f"- {item.content}" for item in results)
        return {self.memory_key: context}

    def save_context(self, inputs: dict[str, Any],
                     outputs: dict[str, str]) -> None:
        """Store the conversation exchange as a memory."""
        user_input = inputs.get(self.input_key, "")
        assistant_output = outputs.get(self.output_key, "")
        if user_input or assistant_output:
            content = f"User: {user_input}\nAssistant: {assistant_output}"
            self._memory.store(
                content=content,
                auto_evaluate=True,
                metadata={"source": "langchain"},
            )

    def clear(self) -> None:
        """No-op for persistent memory."""
        pass
