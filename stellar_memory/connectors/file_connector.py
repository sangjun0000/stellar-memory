"""Local file ingestion connector."""

from __future__ import annotations

import logging
from pathlib import Path

from stellar_memory.connectors import KnowledgeConnector
from stellar_memory.models import IngestResult

logger = logging.getLogger(__name__)

_TEXT_EXTENSIONS = {
    ".txt", ".md", ".rst", ".csv", ".json", ".yaml", ".yml",
    ".py", ".js", ".ts", ".html", ".css", ".xml", ".log",
}


class FileConnector(KnowledgeConnector):
    """Reads local text files and creates memories."""

    def __init__(self, summarizer=None):
        self._summarizer = summarizer
        self._watcher = None

    def can_handle(self, source: str) -> bool:
        p = Path(source)
        return p.exists() and p.suffix.lower() in _TEXT_EXTENSIONS

    def ingest(self, source: str, **kwargs) -> IngestResult:
        p = Path(source)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {source}")
        text = p.read_text(encoding="utf-8", errors="replace")

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
            source_url=f"file://{p.resolve()}",
            memory_id="",
            summary_text=summary,
            was_duplicate=False,
            original_length=len(text),
        )

    def watch(self, directory: str, pattern: str = "*.md",
              callback=None) -> None:
        """Start watching a directory for file changes (requires watchdog)."""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            logger.warning("watchdog not installed – file watching disabled")
            return

        import fnmatch
        connector = self

        class _Handler(FileSystemEventHandler):
            def on_modified(self, event):
                if not event.is_directory and fnmatch.fnmatch(
                    event.src_path, pattern
                ):
                    try:
                        result = connector.ingest(event.src_path)
                        if callback:
                            callback(result)
                    except Exception as e:
                        logger.warning("Watch ingest failed: %s", e)

        observer = Observer()
        observer.schedule(_Handler(), directory, recursive=False)
        observer.start()
        self._watcher = observer

    def stop_watch(self) -> None:
        if self._watcher:
            self._watcher.stop()
            self._watcher = None
