"""Namespace management for multi-tenant memory isolation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.config import StellarConfig


class NamespaceManager:
    """Manages isolated memory namespaces."""

    def __init__(self, base_path: str = "stellar_data"):
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def get_db_path(self, namespace: str) -> str:
        """Get the database path for a namespace."""
        safe_name = self._sanitize(namespace)
        ns_dir = self._base_path / safe_name
        ns_dir.mkdir(parents=True, exist_ok=True)
        return str(ns_dir / "memory.db")

    def list_namespaces(self) -> list[str]:
        """List all existing namespaces."""
        if not self._base_path.exists():
            return []
        return [
            d.name for d in self._base_path.iterdir()
            if d.is_dir() and (d / "memory.db").exists()
        ]

    def delete_namespace(self, namespace: str) -> bool:
        """Delete a namespace and all its data."""
        import shutil
        safe_name = self._sanitize(namespace)
        ns_dir = self._base_path / safe_name
        if ns_dir.exists():
            shutil.rmtree(ns_dir)
            return True
        return False

    def _sanitize(self, name: str) -> str:
        """Sanitize namespace name for filesystem safety."""
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
