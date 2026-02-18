"""Dashboard module for Stellar Memory (P6)."""

from __future__ import annotations

__all__ = ["create_app", "start_dashboard"]


def create_app(stellar_memory=None):
    """Create FastAPI dashboard app."""
    from stellar_memory.dashboard.app import create_app as _create
    return _create(stellar_memory)


def start_dashboard(stellar_memory=None, host: str = "127.0.0.1",
                    port: int = 8080) -> None:
    """Start dashboard in a background thread."""
    from stellar_memory.dashboard.app import start_dashboard as _start
    _start(stellar_memory, host, port)
