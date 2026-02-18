"""Tests for P9-F3: Multimodal Memory."""

import pytest

from stellar_memory.multimodal import (
    TextHandler, CodeHandler, JsonHandler,
    get_handler, ContentTypeHandler, CONTENT_TYPE_HANDLERS,
)
from stellar_memory.models import MemoryItem


def _make_item(content_type: str = "text", metadata: dict | None = None) -> MemoryItem:
    import time
    return MemoryItem(
        id="test_1",
        content="test content",
        created_at=time.time(),
        last_recalled_at=time.time(),
        metadata=metadata or {},
        content_type=content_type,
    )


class TestTextHandler:
    def test_preprocess_string(self):
        h = TextHandler()
        assert h.preprocess("hello world") == "hello world"

    def test_preprocess_dict(self):
        h = TextHandler()
        result = h.preprocess({"key": "value"})
        assert "key" in result

    def test_get_metadata(self):
        h = TextHandler()
        meta = h.get_metadata("hello world foo bar")
        assert meta["word_count"] == 4

    def test_matches_filter_always_true(self):
        h = TextHandler()
        item = _make_item()
        assert h.matches_filter(item, {}) is True
        assert h.matches_filter(item, {"anything": "value"}) is True


class TestCodeHandler:
    def setup_method(self):
        self.handler = CodeHandler()

    def test_detect_python(self):
        code = "def hello():\n    print('hello')\n\nclass MyClass:\n    pass"
        meta = self.handler.get_metadata(code)
        assert meta["language"] == "python"

    def test_detect_javascript(self):
        code = "const app = () => {\n  return null;\n};\nfunction main() {}"
        meta = self.handler.get_metadata(code)
        assert meta["language"] == "javascript"

    def test_detect_sql(self):
        code = "SELECT * FROM users WHERE active = 1 ORDER BY name"
        meta = self.handler.get_metadata(code)
        assert meta["language"] == "sql"

    def test_detect_unknown(self):
        code = "just some random text"
        meta = self.handler.get_metadata(code)
        assert meta["language"] == "unknown"

    def test_extract_python_functions(self):
        code = "def foo():\n    pass\n\ndef bar():\n    pass\n\nclass Baz:\n    pass"
        meta = self.handler.get_metadata(code)
        assert "foo" in meta["functions"]
        assert "bar" in meta["functions"]
        assert "Baz" in meta["functions"]

    def test_extract_js_functions(self):
        code = "function hello() {}\nconst greet = async () => {}"
        meta = self.handler.get_metadata(code)
        assert "hello" in meta["functions"]

    def test_line_count(self):
        code = "line1\nline2\nline3"
        meta = self.handler.get_metadata(code)
        assert meta["line_count"] == 3

    def test_preprocess_returns_string(self):
        assert self.handler.preprocess("code") == "code"

    def test_matches_filter_by_language(self):
        item = _make_item(content_type="code", metadata={"language": "python"})
        assert self.handler.matches_filter(item, {"language": "python"}) is True
        assert self.handler.matches_filter(item, {"language": "javascript"}) is False

    def test_matches_filter_no_language(self):
        item = _make_item(content_type="code")
        assert self.handler.matches_filter(item, {}) is True


class TestJsonHandler:
    def setup_method(self):
        self.handler = JsonHandler()

    def test_preprocess_dict(self):
        data = {"name": "Alice", "age": 30}
        result = self.handler.preprocess(data)
        assert '"name": "Alice"' in result
        assert '"age": 30' in result

    def test_preprocess_string(self):
        result = self.handler.preprocess('{"key": "value"}')
        assert result == '{"key": "value"}'

    def test_get_metadata_from_dict(self):
        data = {"name": "Alice", "age": 30, "active": True}
        meta = self.handler.get_metadata(data)
        assert "name" in meta["keys"]
        assert meta["types"]["name"] == "str"
        assert meta["types"]["age"] == "int"
        assert meta["types"]["active"] == "bool"

    def test_get_metadata_from_json_string(self):
        data = '{"name": "Alice"}'
        meta = self.handler.get_metadata(data)
        assert "name" in meta["keys"]

    def test_get_metadata_invalid_json(self):
        meta = self.handler.get_metadata("not json at all")
        assert meta == {}

    def test_matches_filter_has_key(self):
        item = _make_item(metadata={"keys": ["name", "age"]})
        assert self.handler.matches_filter(item, {"has_key": "name"}) is True
        assert self.handler.matches_filter(item, {"has_key": "email"}) is False

    def test_matches_filter_no_params(self):
        item = _make_item()
        assert self.handler.matches_filter(item, {}) is True


class TestGetHandler:
    def test_text_handler(self):
        h = get_handler("text")
        assert isinstance(h, TextHandler)

    def test_code_handler(self):
        h = get_handler("code")
        assert isinstance(h, CodeHandler)

    def test_json_handler(self):
        h = get_handler("json")
        assert isinstance(h, JsonHandler)

    def test_structured_handler(self):
        h = get_handler("structured")
        assert isinstance(h, JsonHandler)

    def test_unknown_fallback(self):
        h = get_handler("unknown_type")
        assert isinstance(h, TextHandler)

    def test_all_handlers_are_content_type_handler(self):
        for name, handler in CONTENT_TYPE_HANDLERS.items():
            assert isinstance(handler, ContentTypeHandler)
