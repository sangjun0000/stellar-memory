"""Local Data Scanner - discovers importable files on the user's computer.

Scans categories: documents, notes, AI configs, chat history, code, bookmarks.
All scanning requires explicit user consent.
"""

from __future__ import annotations

import logging
import platform
from dataclasses import dataclass, field
from pathlib import Path

from stellar_memory.models import ScanResult, ScanSummary

logger = logging.getLogger(__name__)


@dataclass
class ScanCategory:
    """Definition of a scan category."""
    name: str
    search_paths: list[str]
    file_patterns: list[str]
    importance: float
    recursive: bool = True


# ── Category Definitions ──────────────────────────────────────

CATEGORIES: dict[str, ScanCategory] = {
    "documents": ScanCategory(
        name="Documents",
        search_paths=["Documents", "Desktop"],
        file_patterns=["*.txt", "*.md", "*.rst"],
        importance=0.5,
    ),
    "notes": ScanCategory(
        name="Notes",
        search_paths=["Obsidian", "Notes", ".logseq", "Notion"],
        file_patterns=["*.md"],
        importance=0.7,
    ),
    "ai-config": ScanCategory(
        name="AI Configurations",
        search_paths=["."],
        file_patterns=[],  # handled by _scan_ai_configs
        importance=0.9,
    ),
    "chat-history": ScanCategory(
        name="AI Chat History",
        search_paths=[],  # platform-dependent, set in __init__
        file_patterns=["*.json", "*.jsonl"],
        importance=0.6,
    ),
    "code": ScanCategory(
        name="Code Projects",
        search_paths=["Projects", "repos", "dev", "workspace"],
        file_patterns=["README.md"],
        importance=0.5,
        recursive=False,
    ),
    "bookmarks": ScanCategory(
        name="Browser Bookmarks",
        search_paths=[],  # platform-dependent, set in __init__
        file_patterns=["Bookmarks"],
        importance=0.3,
    ),
}

# AI config files to discover
AI_CONFIG_FILES: dict[str, str] = {
    "CLAUDE.md": "claude",
    ".cursorrules": "cursor",
    ".windsurfrules": "windsurf",
}
AI_CONFIG_SUBPATHS: dict[str, str] = {
    ".github/copilot-instructions.md": "copilot",
}
CLAUDE_MEMORY_DIR = ".claude/memory"

# Files/dirs to always skip
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", "venv", ".venv",
    "dist", "build", ".tox", ".mypy_cache", ".pytest_cache",
    "target", ".next", ".nuxt", "coverage",
}
SENSITIVE_NAMES = {
    "id_rsa", "id_ed25519", "id_dsa", ".ssh",
    "credentials", "credentials.json", "secrets",
    ".env", ".env.local", ".env.production",
    "password", "passwords", "token", "tokens",
}
SENSITIVE_EXTENSIONS = {".pem", ".key", ".pfx", ".p12"}


class LocalScanner:
    """Discovers importable files on the user's computer."""

    MAX_FILE_SIZE = 102_400  # 100KB
    MAX_DEPTH = 3

    def __init__(self, categories: list[str] | None = None,
                 exclude_paths: list[str] | None = None,
                 max_file_size: int | None = None,
                 max_depth: int | None = None):
        self._exclude = set(exclude_paths or [])
        if max_file_size is not None:
            self.MAX_FILE_SIZE = max_file_size
        if max_depth is not None:
            self.MAX_DEPTH = max_depth
        self._home = Path.home()
        self._setup_platform_paths()

    def _setup_platform_paths(self):
        """Set platform-dependent search paths."""
        system = platform.system()
        if system == "Windows":
            CATEGORIES["chat-history"].search_paths = [
                "AppData/Roaming/Claude/logs",
            ]
            CATEGORIES["bookmarks"].search_paths = [
                "AppData/Local/Google/Chrome/User Data/Default",
                "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default",
                "AppData/Local/Microsoft/Edge/User Data/Default",
            ]
        elif system == "Darwin":
            CATEGORIES["chat-history"].search_paths = [
                "Library/Application Support/Claude/logs",
            ]
            CATEGORIES["bookmarks"].search_paths = [
                "Library/Application Support/Google/Chrome/Default",
                "Library/Application Support/BraveSoftware/Brave-Browser/Default",
            ]
        else:  # Linux
            CATEGORIES["chat-history"].search_paths = [
                ".config/claude/logs",
            ]
            CATEGORIES["bookmarks"].search_paths = [
                ".config/google-chrome/Default",
                ".config/BraveSoftware/Brave-Browser/Default",
            ]

    def scan(self, categories: list[str] | None = None) -> ScanSummary:
        """Scan selected categories. Returns results for user review."""
        cats = categories or list(CATEGORIES.keys())
        all_results: list[ScanResult] = []
        by_category: dict[str, int] = {}
        skipped = 0

        for cat_name in cats:
            if cat_name not in CATEGORIES:
                logger.warning("Unknown category: %s", cat_name)
                continue

            if cat_name == "ai-config":
                results = self._scan_ai_configs()
            else:
                results = self._scan_category(cat_name)

            importable = [r for r in results if r.importable]
            by_category[cat_name] = len(importable)
            skipped += len(results) - len(importable)
            all_results.extend(importable)

        total_size = sum(r.size for r in all_results)
        return ScanSummary(
            total_found=len(all_results),
            by_category=by_category,
            total_size_bytes=total_size,
            skipped_count=skipped,
            results=all_results,
        )

    def _scan_category(self, category: str) -> list[ScanResult]:
        """Scan a single category."""
        cat = CATEGORIES[category]
        results: list[ScanResult] = []

        for search_path in cat.search_paths:
            base = self._home / search_path
            if not base.exists():
                continue

            for pattern in cat.file_patterns:
                if cat.recursive:
                    matches = list(base.rglob(pattern))
                else:
                    # Only scan 1 level deep for each subdirectory
                    matches = list(base.glob(pattern))
                    for sub in base.iterdir():
                        if sub.is_dir() and sub.name not in SKIP_DIRS:
                            matches.extend(sub.glob(pattern))

                for path in matches:
                    if not self._is_safe(path):
                        results.append(ScanResult(
                            path=str(path), category=category,
                            size=0, preview="", importable=False,
                        ))
                        continue
                    try:
                        size = path.stat().st_size
                        if size > self.MAX_FILE_SIZE:
                            continue
                        preview = self._get_preview(path)
                        results.append(ScanResult(
                            path=str(path), category=category,
                            size=size, preview=preview, importable=True,
                        ))
                    except (PermissionError, OSError) as e:
                        logger.debug("Cannot read %s: %s", path, e)

        return results

    def _scan_ai_configs(self) -> list[ScanResult]:
        """Find all AI configuration files."""
        results: list[ScanResult] = []
        search_dirs = [Path.cwd(), self._home]

        for d in search_dirs:
            # Top-level AI config files
            for filename, tool in AI_CONFIG_FILES.items():
                path = d / filename
                if path.exists() and path.is_file():
                    try:
                        results.append(ScanResult(
                            path=str(path),
                            category="ai-config",
                            size=path.stat().st_size,
                            preview=self._get_preview(path),
                            ai_tool=tool,
                            importable=True,
                        ))
                    except (PermissionError, OSError):
                        pass

            # Subpath configs (e.g., .github/copilot-instructions.md)
            for subpath, tool in AI_CONFIG_SUBPATHS.items():
                path = d / subpath
                if path.exists() and path.is_file():
                    try:
                        results.append(ScanResult(
                            path=str(path),
                            category="ai-config",
                            size=path.stat().st_size,
                            preview=self._get_preview(path),
                            ai_tool=tool,
                            importable=True,
                        ))
                    except (PermissionError, OSError):
                        pass

            # Claude memory directory
            memory_dir = d / CLAUDE_MEMORY_DIR
            if memory_dir.is_dir():
                for md_file in memory_dir.glob("*.md"):
                    try:
                        results.append(ScanResult(
                            path=str(md_file),
                            category="ai-config",
                            size=md_file.stat().st_size,
                            preview=self._get_preview(md_file),
                            ai_tool="claude-memory",
                            importable=True,
                        ))
                    except (PermissionError, OSError):
                        pass

        # Dedup by path
        seen = set()
        unique: list[ScanResult] = []
        for r in results:
            rpath = str(Path(r.path).resolve())
            if rpath not in seen:
                seen.add(rpath)
                unique.append(r)
        return unique

    def _is_safe(self, path: Path) -> bool:
        """Check if file is safe to read."""
        name_lower = path.name.lower()

        # Skip sensitive files
        if name_lower in SENSITIVE_NAMES:
            return False
        if path.suffix.lower() in SENSITIVE_EXTENSIONS:
            return False

        # Skip if any parent is a skip dir
        for parent in path.parents:
            if parent.name in SKIP_DIRS:
                return False

        # Skip if in exclude list
        path_str = str(path)
        for exc in self._exclude:
            if exc in path_str:
                return False

        # Check depth from home
        try:
            rel = path.relative_to(self._home)
            if len(rel.parts) > self.MAX_DEPTH + 2:
                return False
        except ValueError:
            pass

        return True

    def _get_preview(self, path: Path) -> str:
        """Read first 200 chars of file for preview."""
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            return text[:200].strip()
        except Exception:
            return ""
