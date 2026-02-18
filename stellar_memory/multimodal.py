"""P9-F3: Multimodal Memory - content type-specific handling."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod

from stellar_memory.models import MemoryItem


class ContentTypeHandler(ABC):
    """Abstract base for content type handlers."""

    @abstractmethod
    def preprocess(self, content: str | dict) -> str:
        """Preprocess content before storage."""

    @abstractmethod
    def get_metadata(self, content: str | dict) -> dict:
        """Extract type-specific metadata."""

    @abstractmethod
    def matches_filter(self, item: MemoryItem, filter_params: dict) -> bool:
        """Check if item matches filter criteria."""


class TextHandler(ContentTypeHandler):
    """Default text handler (same as existing behavior)."""

    def preprocess(self, content: str | dict) -> str:
        return str(content)

    def get_metadata(self, content: str | dict) -> dict:
        text = str(content)
        return {"word_count": len(text.split())}

    def matches_filter(self, item: MemoryItem, filter_params: dict) -> bool:
        return True


class CodeHandler(ContentTypeHandler):
    """Code memory handler with language detection."""

    LANGUAGE_PATTERNS: dict[str, str] = {
        "python": r"(def |class |import |from .+ import|if __name__)",
        "javascript": r"(function |const |let |var |=>|require\(|module\.exports)",
        "typescript": r"(interface |type |\: string|\: number|\: boolean|<[A-Z]\w*>)",
        "sql": r"(SELECT |INSERT |UPDATE |DELETE |CREATE TABLE|ALTER TABLE)",
        "rust": r"(fn |let mut |impl |pub fn |use |mod )",
        "go": r"(func |package |import \(|fmt\.)",
        "java": r"(public class |private |protected |void |System\.out)",
        "html": r"(<html|<div|<span|<body|<!DOCTYPE)",
        "css": r"(\{[^}]*:[^}]*\}|@media|\.[\w-]+\s*\{)",
    }

    def preprocess(self, content: str | dict) -> str:
        return str(content)

    def get_metadata(self, content: str | dict) -> dict:
        code = str(content)
        language = self._detect_language(code)
        return {
            "language": language,
            "functions": self._extract_functions(code, language),
            "line_count": len(code.splitlines()),
        }

    def matches_filter(self, item: MemoryItem, filter_params: dict) -> bool:
        if "language" in filter_params:
            item_lang = (item.metadata or {}).get("language", "")
            return item_lang == filter_params["language"]
        return True

    def _detect_language(self, code: str) -> str:
        """Regex-based language detection."""
        scores: dict[str, int] = {}
        for lang, pattern in self.LANGUAGE_PATTERNS.items():
            matches = re.findall(pattern, code)
            if matches:
                scores[lang] = len(matches)
        if not scores:
            return "unknown"
        return max(scores, key=scores.get)  # type: ignore[arg-type]

    def _extract_functions(self, code: str, language: str) -> list[str]:
        """Extract function/class names."""
        names: list[str] = []
        if language == "python":
            for m in re.finditer(r'(?:def|class)\s+(\w+)', code):
                names.append(m.group(1))
        elif language in ("javascript", "typescript"):
            for m in re.finditer(r'(?:function|class)\s+(\w+)', code):
                names.append(m.group(1))
            for m in re.finditer(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:\(|async)', code):
                names.append(m.group(1))
        elif language == "go":
            for m in re.finditer(r'func\s+(\w+)', code):
                names.append(m.group(1))
        elif language == "rust":
            for m in re.finditer(r'fn\s+(\w+)', code):
                names.append(m.group(1))
        elif language == "java":
            for m in re.finditer(r'(?:class|void|int|String)\s+(\w+)\s*[\({]', code):
                names.append(m.group(1))
        return names


class JsonHandler(ContentTypeHandler):
    """JSON/structured data handler."""

    def preprocess(self, content: str | dict) -> str:
        if isinstance(content, dict):
            return json.dumps(content, ensure_ascii=False, indent=2)
        return str(content)

    def get_metadata(self, content: str | dict) -> dict:
        data = content
        if isinstance(content, str):
            try:
                data = json.loads(content)
            except (json.JSONDecodeError, ValueError):
                return {}
        if isinstance(data, dict):
            return {
                "keys": list(data.keys()),
                "types": {k: type(v).__name__ for k, v in data.items()},
            }
        return {}

    def matches_filter(self, item: MemoryItem, filter_params: dict) -> bool:
        if "has_key" in filter_params:
            keys = (item.metadata or {}).get("keys", [])
            return filter_params["has_key"] in keys
        return True


# Handler registry
CONTENT_TYPE_HANDLERS: dict[str, ContentTypeHandler] = {
    "text": TextHandler(),
    "code": CodeHandler(),
    "json": JsonHandler(),
    "structured": JsonHandler(),
}


def get_handler(content_type: str) -> ContentTypeHandler:
    """Get handler for content type, falling back to TextHandler."""
    return CONTENT_TYPE_HANDLERS.get(content_type, TextHandler())


def detect_content_type(content: str) -> str:
    """Auto-detect content type from content string."""
    stripped = content.strip()
    # Try JSON
    if stripped.startswith(("{", "[")):
        try:
            json.loads(stripped)
            return "json"
        except (json.JSONDecodeError, ValueError):
            pass
    # Try code detection
    code_handler = CodeHandler()
    meta = code_handler.get_metadata(content)
    if meta.get("language", "unknown") != "unknown":
        return "code"
    return "text"
