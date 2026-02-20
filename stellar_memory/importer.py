"""Smart Importer - processes scanned files into Stellar Memory.

Handles chunking, deduplication, AI config parsing, and category-based
importance assignment.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from stellar_memory.models import ChunkInfo, ImportResult, ScanResult

logger = logging.getLogger(__name__)

IMPORTANCE_BY_CATEGORY: dict[str, float] = {
    "ai-config": 0.9,
    "notes": 0.7,
    "chat-history": 0.6,
    "documents": 0.5,
    "code": 0.5,
    "bookmarks": 0.3,
}


class SmartImporter:
    """Processes scan results into Stellar Memory."""

    CHUNK_SIZE = 500
    DEDUP_THRESHOLD = 0.8

    def __init__(self, memory):
        self._memory = memory

    def import_scan_results(self, results: list[ScanResult],
                            progress_callback=None) -> ImportResult:
        """Import all scan results into memory."""
        report = ImportResult()
        total = len(results)

        for i, scan_result in enumerate(results):
            if not scan_result.importable:
                continue
            report.total_processed += 1

            try:
                if scan_result.category == "ai-config":
                    ids = self._import_ai_config(scan_result)
                elif scan_result.category == "bookmarks":
                    ids = self._import_bookmarks(scan_result)
                else:
                    ids = self._import_file(scan_result)

                report.imported += len(ids)
                report.memory_ids.extend(ids)
                cat = scan_result.category
                report.by_category[cat] = report.by_category.get(cat, 0) + len(ids)
            except Exception as e:
                report.skipped_error += 1
                report.errors.append(f"{scan_result.path}: {e}")
                logger.debug("Import error: %s: %s", scan_result.path, e)

            if progress_callback:
                progress_callback(i + 1, total)

        # Compute zone distribution
        for mid in report.memory_ids:
            item = self._memory.get(mid)
            if item:
                z = item.zone
                report.by_zone[z] = report.by_zone.get(z, 0) + 1

        return report

    def _import_file(self, scan_result: ScanResult) -> list[str]:
        """Import a single file. Returns list of created memory IDs."""
        path = Path(scan_result.path)
        content = path.read_text(encoding="utf-8", errors="replace")

        if not content.strip():
            return []

        importance = IMPORTANCE_BY_CATEGORY.get(scan_result.category, 0.5)
        chunks = self._chunk_content(content, scan_result.path)
        ids: list[str] = []
        prev_id: str | None = None

        for chunk in chunks:
            if self._is_duplicate(chunk.content):
                continue

            item = self._memory.store(
                content=chunk.content,
                importance=importance,
                metadata=self._build_metadata(scan_result, chunk),
                auto_evaluate=True,
            )
            ids.append(item.id)

            # Link chunks from same file
            if prev_id and hasattr(self._memory, '_graph') and self._memory._graph:
                try:
                    self._memory._graph.add_edge(item.id, prev_id, "derived_from")
                except Exception:
                    pass
            prev_id = item.id

        return ids

    def _import_ai_config(self, scan_result: ScanResult) -> list[str]:
        """Parse AI config files into individual rule memories."""
        path = Path(scan_result.path)
        content = path.read_text(encoding="utf-8", errors="replace")
        ids: list[str] = []

        if scan_result.ai_tool in ("claude", "cursor", "copilot", "windsurf"):
            rules = self._parse_markdown_rules(content)
            for rule in rules:
                if self._is_duplicate(rule):
                    continue
                item = self._memory.store(
                    content=rule,
                    importance=0.9,
                    metadata={
                        "source": "auto-import",
                        "type": "ai-rule",
                        "ai_tool": scan_result.ai_tool,
                        "file": scan_result.path,
                        "category": "ai-config",
                    },
                    auto_evaluate=False,
                )
                ids.append(item.id)
        elif scan_result.ai_tool == "claude-memory":
            if self._is_duplicate(content):
                return []
            item = self._memory.store(
                content=content,
                importance=0.85,
                metadata={
                    "source": "auto-import",
                    "type": "ai-learned",
                    "ai_tool": "claude",
                    "file": scan_result.path,
                    "category": "ai-config",
                },
                auto_evaluate=False,
            )
            ids.append(item.id)

        return ids

    def _import_bookmarks(self, scan_result: ScanResult) -> list[str]:
        """Import browser bookmarks."""
        path = Path(scan_result.path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            return []

        bookmarks = self._extract_bookmarks(data)
        ids: list[str] = []
        for bm in bookmarks[:50]:  # cap at 50 bookmarks
            content = f"Bookmark: {bm['name']} - {bm['url']}"
            if self._is_duplicate(content):
                continue
            item = self._memory.store(
                content=content,
                importance=0.3,
                metadata={
                    "source": "auto-import",
                    "type": "bookmark",
                    "category": "bookmarks",
                    "url": bm["url"],
                },
                auto_evaluate=False,
            )
            ids.append(item.id)
        return ids

    def _extract_bookmarks(self, data, depth: int = 0) -> list[dict]:
        """Recursively extract bookmarks from Chrome-format JSON."""
        results: list[dict] = []
        if depth > 5:
            return results
        if isinstance(data, dict):
            if data.get("type") == "url" and "url" in data:
                results.append({"name": data.get("name", ""), "url": data["url"]})
            for key in ("children", "roots", "bookmark_bar", "other", "synced"):
                if key in data:
                    results.extend(self._extract_bookmarks(data[key], depth + 1))
        elif isinstance(data, list):
            for item in data:
                results.extend(self._extract_bookmarks(item, depth + 1))
        return results

    def _chunk_content(self, content: str, source: str) -> list[ChunkInfo]:
        """Split content into chunks at paragraph boundaries."""
        if len(content) <= self.CHUNK_SIZE:
            return [ChunkInfo(content=content.strip(), index=0,
                              total_chunks=1, source_path=source)]

        paragraphs = content.split("\n\n")
        chunks: list[ChunkInfo] = []
        current: list[str] = []
        current_len = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if current_len + len(para) > self.CHUNK_SIZE and current:
                chunks.append(ChunkInfo(
                    content="\n\n".join(current),
                    index=len(chunks),
                    total_chunks=0,  # set after
                    source_path=source,
                ))
                current = [para]
                current_len = len(para)
            else:
                current.append(para)
                current_len += len(para)

        if current:
            chunks.append(ChunkInfo(
                content="\n\n".join(current),
                index=len(chunks),
                total_chunks=0,
                source_path=source,
            ))

        total = len(chunks)
        for c in chunks:
            c.total_chunks = total
        return chunks

    def _is_duplicate(self, content: str) -> bool:
        """Check if similar content already exists."""
        if not content.strip():
            return True
        # Use first 100 chars as query
        query = content[:100]
        results = self._memory.recall(query, limit=3)
        for item in results:
            similarity = self._jaccard_similarity(content, item.content)
            if similarity > self.DEDUP_THRESHOLD:
                return True
        return False

    def _jaccard_similarity(self, a: str, b: str) -> float:
        """Word-level Jaccard similarity."""
        set_a = set(a.lower().split())
        set_b = set(b.lower().split())
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)

    def _parse_markdown_rules(self, content: str) -> list[str]:
        """Split markdown into section-level rules."""
        sections: list[str] = []
        current: list[str] = []
        for line in content.split("\n"):
            if line.startswith(("## ", "### ")) and current:
                text = "\n".join(current).strip()
                if len(text) > 20:
                    sections.append(text)
                current = [line]
            else:
                current.append(line)
        if current:
            text = "\n".join(current).strip()
            if len(text) > 20:
                sections.append(text)
        return sections

    def _build_metadata(self, scan_result: ScanResult,
                        chunk: ChunkInfo | None = None) -> dict:
        """Build metadata dict for a memory item."""
        meta = {
            "source": "auto-import",
            "file": scan_result.path,
            "category": scan_result.category,
        }
        if scan_result.ai_tool:
            meta["ai_tool"] = scan_result.ai_tool
        if chunk and chunk.total_chunks > 1:
            meta["chunk_index"] = chunk.index
            meta["total_chunks"] = chunk.total_chunks
        return meta
