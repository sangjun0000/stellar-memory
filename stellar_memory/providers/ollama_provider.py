"""Ollama local LLM and Embedder providers."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class OllamaLLMProvider:
    """Ollama local LLM provider using HTTP API."""

    def __init__(self, config):
        self._config = config
        self._base_url = config.base_url or "http://localhost:11434"

    def complete(self, prompt: str, max_tokens: int = 256) -> str:
        import requests
        response = requests.post(
            f"{self._base_url}/api/generate",
            json={
                "model": self._config.model or "llama3",
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens},
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["response"]


class OllamaEmbedderProvider:
    """Ollama local embedding provider using HTTP API."""

    def __init__(self, config):
        self._config = config
        self._base_url = "http://localhost:11434"

    def embed(self, text: str) -> list[float]:
        import requests
        response = requests.post(
            f"{self._base_url}/api/embed",
            json={
                "model": self._config.model_name or "nomic-embed-text",
                "input": text,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["embeddings"][0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


def create_ollama_llm(config) -> OllamaLLMProvider:
    import requests  # noqa: F401 - ensure package is available
    return OllamaLLMProvider(config)


def create_ollama_embedder(config) -> OllamaEmbedderProvider:
    import requests  # noqa: F401
    return OllamaEmbedderProvider(config)
