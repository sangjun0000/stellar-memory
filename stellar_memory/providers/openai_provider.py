"""OpenAI LLM and Embedder providers."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


class OpenAILLMProvider:
    """OpenAI GPT-based LLM provider."""

    def __init__(self, config):
        self._config = config
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            from openai import OpenAI
            api_key = os.environ.get(self._config.api_key_env, "")
            self._client = OpenAI(api_key=api_key)

    def complete(self, prompt: str, max_tokens: int = 256) -> str:
        self._ensure_client()
        response = self._client.chat.completions.create(
            model=self._config.model or "gpt-4o-mini",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content


class OpenAIEmbedderProvider:
    """OpenAI text-embedding provider."""

    def __init__(self, config):
        self._config = config
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            from openai import OpenAI
            api_key = os.environ.get("OPENAI_API_KEY", "")
            self._client = OpenAI(api_key=api_key)

    def embed(self, text: str) -> list[float]:
        self._ensure_client()
        response = self._client.embeddings.create(
            model=self._config.model_name or "text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self._ensure_client()
        response = self._client.embeddings.create(
            model=self._config.model_name or "text-embedding-3-small",
            input=texts,
        )
        return [d.embedding for d in response.data]


def create_openai_llm(config) -> OpenAILLMProvider:
    import openai  # noqa: F401 - ensure package is installed
    return OpenAILLMProvider(config)


def create_openai_embedder(config) -> OpenAIEmbedderProvider:
    import openai  # noqa: F401
    return OpenAIEmbedderProvider(config)
