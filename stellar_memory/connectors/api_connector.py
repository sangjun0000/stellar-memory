"""REST API ingestion connector."""

from __future__ import annotations

import json
import logging

from stellar_memory.connectors import KnowledgeConnector
from stellar_memory.models import IngestResult

logger = logging.getLogger(__name__)


class ApiConnector(KnowledgeConnector):
    """Fetches JSON from a REST API and creates a memory."""

    def __init__(self, summarizer=None):
        self._summarizer = summarizer
        self._subscriptions: dict[str, float] = {}  # url -> interval

    def can_handle(self, source: str) -> bool:
        return source.startswith("api://") or source.startswith("api+http")

    def ingest(self, source: str, **kwargs) -> IngestResult:
        try:
            import httpx
        except ImportError:
            raise ImportError(
                "httpx is required for API ingestion. "
                "Install with: pip install stellar-memory[connectors]"
            )
        url = source.replace("api://", "https://").replace(
            "api+http://", "http://").replace("api+https://", "https://")
        headers = kwargs.get("headers", {})
        resp = httpx.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        try:
            data = resp.json()
            text = json.dumps(data, ensure_ascii=False, indent=2)
        except Exception:
            text = resp.text

        summary = text
        if self._summarizer and len(text) > 100:
            try:
                result = self._summarizer.summarize(text)
                if result:
                    summary = result
            except Exception:
                pass
        if len(summary) > 500:
            summary = summary[:500]

        return IngestResult(
            source_url=source,
            memory_id="",
            summary_text=summary,
            was_duplicate=False,
            original_length=len(text),
        )

    def subscribe(self, url: str, interval: float = 3600) -> None:
        """Register a URL for periodic ingestion."""
        self._subscriptions[url] = interval
