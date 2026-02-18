"""Tests for P5-F3: AI Memory Summarization."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from stellar_memory.summarizer import MemorySummarizer
from stellar_memory.config import SummarizationConfig, LLMConfig, StellarConfig
from stellar_memory.stellar import StellarMemory


class TestShouldSummarize:
    def test_long_content_returns_true(self):
        config = SummarizationConfig(enabled=True, min_length=50)
        summarizer = MemorySummarizer(config, LLMConfig())
        assert summarizer.should_summarize("x" * 100) is True

    def test_short_content_returns_false(self):
        config = SummarizationConfig(enabled=True, min_length=50)
        summarizer = MemorySummarizer(config, LLMConfig())
        assert summarizer.should_summarize("short") is False

    def test_exact_threshold_returns_true(self):
        config = SummarizationConfig(enabled=True, min_length=10)
        summarizer = MemorySummarizer(config, LLMConfig())
        assert summarizer.should_summarize("1234567890") is True

    def test_disabled_returns_false(self):
        config = SummarizationConfig(enabled=False, min_length=5)
        summarizer = MemorySummarizer(config, LLMConfig())
        assert summarizer.should_summarize("x" * 100) is False


class TestSummarize:
    def test_summarize_calls_llm(self):
        config = SummarizationConfig(enabled=True, min_length=10, max_summary_length=50)
        summarizer = MemorySummarizer(config, LLMConfig())
        mock_llm = MagicMock()
        mock_llm.complete.return_value = "  A concise summary  "
        summarizer._llm = mock_llm

        result = summarizer.summarize("x" * 100)
        assert result == "A concise summary"
        mock_llm.complete.assert_called_once()

    def test_summarize_truncates_to_max_length(self):
        config = SummarizationConfig(enabled=True, min_length=10, max_summary_length=10)
        summarizer = MemorySummarizer(config, LLMConfig())
        mock_llm = MagicMock()
        mock_llm.complete.return_value = "This is a very long summary text"
        summarizer._llm = mock_llm

        result = summarizer.summarize("x" * 100)
        assert len(result) <= 10

    def test_summarize_returns_none_for_short(self):
        config = SummarizationConfig(enabled=True, min_length=500)
        summarizer = MemorySummarizer(config, LLMConfig())
        result = summarizer.summarize("short text")
        assert result is None

    def test_summarize_returns_none_on_llm_failure(self):
        config = SummarizationConfig(enabled=True, min_length=10)
        summarizer = MemorySummarizer(config, LLMConfig())
        mock_llm = MagicMock()
        mock_llm.complete.side_effect = RuntimeError("API error")
        summarizer._llm = mock_llm

        result = summarizer.summarize("x" * 100)
        assert result is None

    def test_summarize_lazy_loads_llm(self):
        config = SummarizationConfig(enabled=True, min_length=10)
        summarizer = MemorySummarizer(config, LLMConfig())
        assert summarizer._llm is None
        # Since no real provider, should fail gracefully
        result = summarizer.summarize("x" * 100)
        assert result is None


class TestSummarizerPrompt:
    def test_prompt_template_format(self):
        config = SummarizationConfig(enabled=True, min_length=10, max_summary_length=100)
        text = "The quick brown fox jumps over the lazy dog."
        prompt = MemorySummarizer.PROMPT_TEMPLATE.format(
            max_len=100, content=text
        )
        assert "100" in prompt
        assert text in prompt
        assert "Summary:" in prompt


class TestStellarMemoryWithSummarizer:
    def test_store_without_summarization(self):
        """Short content should not trigger summarization."""
        config = StellarConfig(
            db_path=":memory:",
            summarization=SummarizationConfig(enabled=True, min_length=1000),
        )
        config.graph.persistent = False
        config.embedder.enabled = False
        config.event_logger.enabled = False
        mem = StellarMemory(config)
        item = mem.store("short text")
        assert item.content == "short text"

    def test_store_with_skip_summarize(self):
        """skip_summarize=True should bypass summarization."""
        config = StellarConfig(
            db_path=":memory:",
            summarization=SummarizationConfig(enabled=True, min_length=5),
        )
        config.graph.persistent = False
        config.embedder.enabled = False
        config.event_logger.enabled = False
        mem = StellarMemory(config)
        item = mem.store("This is a long enough content for testing", skip_summarize=True)
        assert "[Summary]" not in item.content

    def test_summarizer_disabled(self):
        """Disabled summarization should not create summarizer."""
        config = StellarConfig(
            db_path=":memory:",
            summarization=SummarizationConfig(enabled=False),
        )
        config.graph.persistent = False
        config.embedder.enabled = False
        config.event_logger.enabled = False
        mem = StellarMemory(config)
        assert mem._summarizer is None
