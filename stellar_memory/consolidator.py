"""Memory consolidation - merge similar memories to prevent redundancy."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from stellar_memory.models import MemoryItem, ConsolidationResult
from stellar_memory.utils import cosine_similarity

if TYPE_CHECKING:
    from stellar_memory.config import ConsolidationConfig


class MemoryConsolidator:
    def __init__(self, config: ConsolidationConfig, embedder):
        self._config = config
        self._embedder = embedder

    def find_similar(self, new_item: MemoryItem,
                     candidates: list[MemoryItem]) -> MemoryItem | None:
        """Find the most similar existing item above threshold."""
        if new_item.embedding is None:
            return None
        best_match = None
        best_score = 0.0
        for candidate in candidates:
            if candidate.embedding is None or candidate.id == new_item.id:
                continue
            score = cosine_similarity(new_item.embedding, candidate.embedding)
            if score >= self._config.similarity_threshold and score > best_score:
                best_score = score
                best_match = candidate
        return best_match

    def merge(self, existing: MemoryItem, new_item: MemoryItem) -> MemoryItem:
        """Merge new_item into existing. Returns updated existing."""
        if new_item.content not in existing.content:
            merged_content = f"{existing.content}\n---\n{new_item.content}"
            if len(merged_content) <= self._config.max_content_length:
                existing.content = merged_content
        existing.recall_count += new_item.recall_count
        existing.arbitrary_importance = max(
            existing.arbitrary_importance, new_item.arbitrary_importance
        )
        new_embedding = self._embedder.embed(existing.content)
        if new_embedding is not None:
            existing.embedding = new_embedding
        merge_history = existing.metadata.get("merged_from", [])
        merge_history.append(new_item.id)
        existing.metadata["merged_from"] = merge_history
        existing.metadata["last_merged_at"] = time.time()
        return existing

    def consolidate_zone(self, items: list[MemoryItem]) -> ConsolidationResult:
        """Batch-merge all similar items in a zone."""
        result = ConsolidationResult()
        merged_ids: set[str] = set()
        for i, item_a in enumerate(items):
            if item_a.id in merged_ids:
                continue
            for item_b in items[i + 1:]:
                if item_b.id in merged_ids:
                    continue
                if (item_a.embedding is not None and item_b.embedding is not None
                        and cosine_similarity(item_a.embedding, item_b.embedding)
                        >= self._config.similarity_threshold):
                    self.merge(item_a, item_b)
                    merged_ids.add(item_b.id)
                    result.merged_count += 1
            result.skipped_count += 1
        return result
