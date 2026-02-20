"""LangChain adapter for Celestial Memory Engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from celestial_engine import CelestialMemory


class LangChainAdapter:
    """Integrates CelestialMemory with LangChain framework.

    Usage:
        from celestial_engine import CelestialMemory
        from celestial_engine.adapters import LangChainAdapter

        memory = CelestialMemory()
        retriever = LangChainAdapter(memory).as_retriever(k=5)
    """

    def __init__(self, memory: CelestialMemory) -> None:
        self._memory = memory

    def as_retriever(self, k: int = 5):
        """Return a LangChain BaseRetriever backed by celestial memory."""
        from langchain_core.documents import Document
        from langchain_core.retrievers import BaseRetriever

        mem = self._memory

        class CelestialRetriever(BaseRetriever):
            def _get_relevant_documents(self, query: str, **kwargs):
                results = mem.recall(query, limit=k)
                return [
                    Document(page_content=r.content, metadata=r.metadata)
                    for r in results
                ]

        return CelestialRetriever()

    def as_memory(self):
        """Return a LangChain ConversationBufferMemory backed by celestial memory."""
        from langchain.memory import ConversationBufferMemory

        mem = self._memory

        class CelestialConversationMemory(ConversationBufferMemory):
            def save_context(self, inputs, outputs):
                content = (
                    f"Human: {inputs.get('input', '')}\n"
                    f"AI: {outputs.get('output', '')}"
                )
                mem.store(content)

            def load_memory_variables(self, inputs):
                query = inputs.get("input", "")
                results = mem.recall(query, limit=3)
                history = "\n".join(r.content for r in results)
                return {self.memory_key: history}

        return CelestialConversationMemory()
