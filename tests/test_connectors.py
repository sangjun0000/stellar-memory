"""Tests for P6 connectors module: Web, File, API connectors."""

import os
import tempfile
import pytest

from stellar_memory.connectors.file_connector import FileConnector
from stellar_memory.connectors.web_connector import WebConnector
from stellar_memory.connectors.api_connector import ApiConnector


class TestFileConnector:
    def test_can_handle_txt(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test content")
            path = f.name
        try:
            fc = FileConnector()
            assert fc.can_handle(path)
        finally:
            os.unlink(path)

    def test_cannot_handle_nonexistent(self):
        fc = FileConnector()
        assert not fc.can_handle("/tmp/nonexistent_file_12345.txt")

    def test_cannot_handle_binary(self):
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
            f.write(b"\x00\x01\x02")
            path = f.name
        try:
            fc = FileConnector()
            assert not fc.can_handle(path)
        finally:
            os.unlink(path)

    def test_ingest(self):
        with tempfile.NamedTemporaryFile(
            suffix=".md", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write("# Hello World\nThis is a test file for ingestion.")
            path = f.name
        try:
            fc = FileConnector()
            result = fc.ingest(path)
            assert "Hello World" in result.summary_text
            assert result.original_length > 0
            assert result.memory_id == ""
        finally:
            os.unlink(path)

    def test_ingest_nonexistent_raises(self):
        fc = FileConnector()
        with pytest.raises(FileNotFoundError):
            fc.ingest("/tmp/does_not_exist_98765.txt")

    def test_ingest_unicode(self):
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write("한국어 파일 내용 테스트")
            path = f.name
        try:
            fc = FileConnector()
            result = fc.ingest(path)
            assert "한국어" in result.summary_text
        finally:
            os.unlink(path)

    def test_can_handle_multiple_extensions(self):
        fc = FileConnector()
        for ext in [".py", ".json", ".yaml", ".csv", ".log"]:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                f.write(b"content")
                path = f.name
            try:
                assert fc.can_handle(path), f"Should handle {ext}"
            finally:
                os.unlink(path)


class TestWebConnector:
    def test_can_handle_http(self):
        wc = WebConnector()
        assert wc.can_handle("http://example.com")
        assert wc.can_handle("https://example.com/page")
        assert not wc.can_handle("ftp://example.com")
        assert not wc.can_handle("/local/path.html")

    def test_extract_text(self):
        html = """
        <html>
        <head><title>Test</title></head>
        <body>
        <script>var x=1;</script>
        <style>.a{color:red}</style>
        <p>Hello World</p>
        </body>
        </html>
        """
        text = WebConnector._extract_text(html)
        assert "Hello World" in text
        assert "var x" not in text
        assert "color:red" not in text

    def test_extract_text_plain(self):
        text = WebConnector._extract_text("<p>Simple</p>")
        assert "Simple" in text


class TestApiConnector:
    def test_can_handle(self):
        ac = ApiConnector()
        assert ac.can_handle("api://example.com/v1/data")
        assert ac.can_handle("api+https://example.com/v1/data")
        assert not ac.can_handle("https://example.com/api")
        assert not ac.can_handle("/local/file.json")


class TestConnectorInterface:
    """Test that all connectors have the expected interface."""
    def test_file_connector_is_knowledge_connector(self):
        from stellar_memory.connectors import KnowledgeConnector
        fc = FileConnector()
        assert isinstance(fc, KnowledgeConnector)

    def test_web_connector_is_knowledge_connector(self):
        from stellar_memory.connectors import KnowledgeConnector
        wc = WebConnector()
        assert isinstance(wc, KnowledgeConnector)

    def test_api_connector_is_knowledge_connector(self):
        from stellar_memory.connectors import KnowledgeConnector
        ac = ApiConnector()
        assert isinstance(ac, KnowledgeConnector)


class TestConnectorSummarizer:
    """Test summarizer integration in connectors."""

    def test_file_connector_with_summarizer(self):
        from unittest.mock import MagicMock
        summarizer = MagicMock()
        summarizer.summarize.return_value = "Summarized content"
        fc = FileConnector(summarizer=summarizer)
        assert fc._summarizer is summarizer

    def test_web_connector_with_summarizer(self):
        from unittest.mock import MagicMock
        summarizer = MagicMock()
        wc = WebConnector(summarizer=summarizer, consolidator=None)
        assert wc._summarizer is summarizer
        assert wc._consolidator is None

    def test_api_connector_with_summarizer(self):
        from unittest.mock import MagicMock
        summarizer = MagicMock()
        ac = ApiConnector(summarizer=summarizer)
        assert ac._summarizer is summarizer

    def test_file_connector_summarizer_called_on_long_text(self):
        from unittest.mock import MagicMock
        summarizer = MagicMock()
        summarizer.summarize.return_value = "Short summary"
        fc = FileConnector(summarizer=summarizer)
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write("x" * 200)  # > 100 chars triggers summarizer
            path = f.name
        try:
            result = fc.ingest(path)
            summarizer.summarize.assert_called_once()
            assert result.summary_text == "Short summary"
        finally:
            os.unlink(path)


class TestFileConnectorWatch:
    def test_watch_method_exists(self):
        fc = FileConnector()
        assert hasattr(fc, "watch")
        assert hasattr(fc, "stop_watch")

    def test_file_source_url_prefix(self):
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write("file prefix test")
            path = f.name
        try:
            fc = FileConnector()
            result = fc.ingest(path)
            assert result.source_url.startswith("file://")
        finally:
            os.unlink(path)


class TestApiConnectorSubscribe:
    def test_subscribe_method(self):
        ac = ApiConnector()
        ac.subscribe("api://example.com/data", interval=1800)
        assert "api://example.com/data" in ac._subscriptions
        assert ac._subscriptions["api://example.com/data"] == 1800
