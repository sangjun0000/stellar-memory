"""Web page ingestion connector."""

from __future__ import annotations

import hashlib
import logging
import time

from stellar_memory.connectors import KnowledgeConnector
from stellar_memory.models import IngestResult

logger = logging.getLogger(__name__)


class WebConnector(KnowledgeConnector):
    """Fetches a web page, extracts text, and creates a memory."""

    def __init__(self, summarizer=None, consolidator=None):
        self._summarizer = summarizer
        self._consolidator = consolidator

    def can_handle(self, source: str) -> bool:
        return source.startswith("http://") or source.startswith("https://")

    def ingest(self, source: str, **kwargs) -> IngestResult:
        try:
            import httpx
        except ImportError:
            raise ImportError(
                "httpx is required for web ingestion. "
                "Install with: pip install stellar-memory[connectors]"
            )
        resp = httpx.get(source, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        text = self._extract_text(resp.text)

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

    @staticmethod
    def _extract_text(html: str) -> str:
        """Simple HTML-to-text extraction."""
        import re
        text = re.sub(r"<script[^>]*>.*?</script>", "", html,
                      flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text,
                      flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
