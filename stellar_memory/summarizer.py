"""AI-powered memory summarization."""

from __future__ import annotations

import logging

from stellar_memory.config import SummarizationConfig, LLMConfig

logger = logging.getLogger(__name__)


class MemorySummarizer:
    """Summarize long memories using LLM."""

    PROMPT_TEMPLATE = (
        "Summarize the following text in one concise sentence "
        "(max {max_len} characters). Keep only the essential facts, "
        "dates, names, and action items.\n\n"
        "Text: {content}\n\n"
        "Summary:"
    )

    def __init__(self, config: SummarizationConfig, llm_config: LLMConfig):
        self._config = config
        self._llm_config = llm_config
        self._llm = None

    def should_summarize(self, content: str) -> bool:
        """Check if content is long enough to warrant summarization."""
        return (self._config.enabled
                and len(content) >= self._config.min_length)

    def summarize(self, content: str) -> str | None:
        """Generate a summary using LLM. Returns None on failure."""
        if not self.should_summarize(content):
            return None
        try:
            if self._llm is None:
                from stellar_memory.providers import ProviderRegistry
                self._llm = ProviderRegistry.create_llm(self._llm_config)
            prompt = self.PROMPT_TEMPLATE.format(
                max_len=self._config.max_summary_length,
                content=content,
            )
            result = self._llm.complete(prompt, max_tokens=self._config.max_summary_length)
            return result.strip()[:self._config.max_summary_length]
        except Exception:
            logger.warning("Summarization failed, storing original")
            return None
