"""AI Knowledge Base - universal brain for all AI tools.

Replaces per-tool config files (CLAUDE.md, .cursorrules, etc.) with
a unified memory store that any AI can query via MCP.
"""

from __future__ import annotations

import json
import logging
import platform
from pathlib import Path

logger = logging.getLogger(__name__)

# Metadata type constants
TYPE_RULE = "ai-rule"
TYPE_CONTEXT = "ai-context"
TYPE_PREFERENCE = "ai-preference"
TYPE_GUIDE = "ai-guide"
TYPE_LEARNED = "ai-learned"


class AIKnowledgeBase:
    """Universal AI knowledge store."""

    def __init__(self, memory):
        self._memory = memory

    # ── Project Detection ──────────────────────────────────────

    def detect_project(self, project_path: str | None = None) -> dict:
        """Auto-detect project type, tech stack, and structure."""
        root = Path(project_path or ".").resolve()
        info = {
            "type": "unknown",
            "name": root.name,
            "tech_stack": [],
            "entry_points": [],
            "package_manager": None,
            "test_framework": None,
            "structure": "",
        }

        # Python
        if (root / "pyproject.toml").exists() or (root / "setup.py").exists() \
                or (root / "requirements.txt").exists():
            info["type"] = "python"
            info["tech_stack"].append("python")
            info["package_manager"] = "pip"
            info["test_framework"] = "pytest"
            if (root / "pyproject.toml").exists():
                info.update(self._detect_from_pyproject(root / "pyproject.toml"))

        # Node.js
        if (root / "package.json").exists():
            info["type"] = "node" if info["type"] == "unknown" else "mixed"
            info["tech_stack"].append("node")
            info["package_manager"] = "npm"
            info.update(self._detect_from_package_json(root / "package.json"))

        # Go
        if (root / "go.mod").exists():
            info["type"] = "go" if info["type"] == "unknown" else "mixed"
            info["tech_stack"].append("go")
            info["test_framework"] = "go test"

        # Rust
        if (root / "Cargo.toml").exists():
            info["type"] = "rust" if info["type"] == "unknown" else "mixed"
            info["tech_stack"].append("rust")
            info["package_manager"] = "cargo"

        info["structure"] = self._scan_structure(root)
        return info

    def _detect_from_pyproject(self, path: Path) -> dict:
        """Extract project info from pyproject.toml."""
        extra: dict = {}
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            for line in text.split("\n"):
                line = line.strip()
                if line.startswith("name"):
                    val = line.split("=", 1)[-1].strip().strip('"').strip("'")
                    if val:
                        extra["name"] = val
                elif "fastapi" in line.lower():
                    extra.setdefault("tech_stack_extra", []).append("fastapi")
                elif "django" in line.lower():
                    extra.setdefault("tech_stack_extra", []).append("django")
                elif "flask" in line.lower():
                    extra.setdefault("tech_stack_extra", []).append("flask")
        except Exception:
            pass
        result = {}
        if "name" in extra:
            result["name"] = extra["name"]
        if "tech_stack_extra" in extra:
            result["tech_stack"] = extra["tech_stack_extra"]
        return result

    def _detect_from_package_json(self, path: Path) -> dict:
        """Extract project info from package.json."""
        result: dict = {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if "name" in data:
                result["name"] = data["name"]
            deps = {**data.get("dependencies", {}),
                    **data.get("devDependencies", {})}
            extras = []
            if "react" in deps:
                extras.append("react")
            if "next" in deps:
                extras.append("nextjs")
            if "vue" in deps:
                extras.append("vue")
            if "express" in deps:
                extras.append("express")
            if "typescript" in deps:
                extras.append("typescript")
            if extras:
                result["tech_stack"] = extras
            if "jest" in deps:
                result["test_framework"] = "jest"
            elif "vitest" in deps:
                result["test_framework"] = "vitest"
        except Exception:
            pass
        return result

    def _scan_structure(self, root: Path) -> str:
        """Scan directory structure (top 2 levels)."""
        lines = []
        try:
            for item in sorted(root.iterdir()):
                if item.name.startswith(".") or item.name in (
                    "node_modules", "__pycache__", "venv", ".venv",
                    "dist", "build", ".git",
                ):
                    continue
                if item.is_dir():
                    lines.append(f"{item.name}/")
                    try:
                        for sub in sorted(item.iterdir()):
                            if sub.name.startswith(".") or sub.name == "__pycache__":
                                continue
                            suffix = "/" if sub.is_dir() else ""
                            lines.append(f"  {sub.name}{suffix}")
                    except PermissionError:
                        pass
                else:
                    lines.append(item.name)
        except PermissionError:
            pass
        return "\n".join(lines[:50])  # cap at 50 lines

    # ── Context Generation ─────────────────────────────────────

    def generate_project_context(self, project_path: str | None = None) -> str:
        """Generate and store project context memory. Returns memory ID."""
        info = self.detect_project(project_path)

        tech = ", ".join(info["tech_stack"]) or "N/A"
        entries = "\n".join(f"- {e}" for e in info.get("entry_points", [])) or "N/A"
        context_text = (
            f"## Project: {info['name']}\n"
            f"Type: {info['type']}\n"
            f"Tech Stack: {tech}\n"
            f"Package Manager: {info.get('package_manager') or 'N/A'}\n"
            f"Test Framework: {info.get('test_framework') or 'N/A'}\n\n"
            f"### Directory Structure\n{info.get('structure') or 'N/A'}\n\n"
            f"### Entry Points\n{entries}\n"
        )

        # Remove old context if exists
        existing = self._memory.recall("project context tech stack", limit=3)
        for item in existing:
            if (item.metadata or {}).get("type") == TYPE_CONTEXT:
                self._memory.forget(item.id)

        item = self._memory.store(
            content=context_text,
            importance=self._memory.config.knowledge_base.context_importance,
            metadata={
                "type": TYPE_CONTEXT,
                "source": "auto-detect",
                "project_name": info["name"],
                "project_type": info["type"],
            },
            auto_evaluate=False,
        )
        return item.id

    def get_context(self, project_path: str | None = None) -> str:
        """Retrieve stored project context. If none exists, generate it."""
        results = self._memory.recall("project context tech stack structure", limit=3)
        for item in results:
            if (item.metadata or {}).get("type") == TYPE_CONTEXT:
                return item.content

        # Auto-generate if not found
        self.generate_project_context(project_path)
        results = self._memory.recall("project context tech stack structure", limit=1)
        return results[0].content if results else ""

    # ── Rules & Preferences ────────────────────────────────────

    def get_rules(self) -> list[str]:
        """Get all active coding rules/preferences sorted by importance."""
        results = self._memory.recall("coding rules conventions style guide", limit=20)
        rules = []
        for item in results:
            meta_type = (item.metadata or {}).get("type", "")
            if meta_type in (TYPE_RULE, TYPE_PREFERENCE):
                rules.append(item.content)
        return rules

    def learn_preference(self, key: str, value: str) -> str:
        """Store a user preference. Updates existing if same key. Returns memory ID."""
        # Check for existing preference with same key
        results = self._memory.recall(f"preference {key}", limit=5)
        for item in results:
            meta = item.metadata or {}
            if meta.get("type") == TYPE_PREFERENCE and \
                    meta.get("preference_key") == key:
                self._memory.forget(item.id)

        item = self._memory.store(
            content=f"User preference: {key} = {value}",
            importance=self._memory.config.knowledge_base.preference_importance,
            metadata={
                "type": TYPE_PREFERENCE,
                "source": "user",
                "preference_key": key,
                "preference_value": value,
            },
            auto_evaluate=False,
        )
        return item.id

    def get_preferences(self) -> dict[str, str]:
        """Get all stored preferences as key-value dict."""
        results = self._memory.recall("user preference", limit=50)
        prefs = {}
        for item in results:
            meta = item.metadata or {}
            if meta.get("type") == TYPE_PREFERENCE:
                key = meta.get("preference_key", "")
                value = meta.get("preference_value", "")
                if key:
                    prefs[key] = value
        return prefs

    # ── AI Config Sync ─────────────────────────────────────────

    def sync_ai_config(self, tool: str, config_path: str) -> int:
        """Import an AI config file into Stellar Memory. Returns rule count."""
        path = Path(config_path)
        if not path.exists():
            logger.warning("Config file not found: %s", config_path)
            return 0

        content = path.read_text(encoding="utf-8", errors="replace")
        rules = self._parse_markdown_rules(content)
        count = 0

        for rule in rules:
            # Simple dedup check
            existing = self._memory.recall(rule[:100], limit=2)
            is_dup = False
            for item in existing:
                if (item.metadata or {}).get("type") == TYPE_RULE:
                    overlap = self._jaccard(rule, item.content)
                    if overlap > 0.8:
                        is_dup = True
                        break
            if is_dup:
                continue

            self._memory.store(
                content=rule,
                importance=self._memory.config.knowledge_base.rule_importance,
                metadata={
                    "type": TYPE_RULE,
                    "source": "ai-config-sync",
                    "ai_tool": tool,
                    "file": str(path),
                    "category": "ai-config",
                },
                auto_evaluate=False,
            )
            count += 1

        return count

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

    def _jaccard(self, a: str, b: str) -> float:
        """Word-level Jaccard similarity."""
        set_a = set(a.lower().split())
        set_b = set(b.lower().split())
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union)
