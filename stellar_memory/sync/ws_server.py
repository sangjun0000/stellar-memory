"""WebSocket server for memory sync."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.sync.sync_manager import MemorySyncManager

logger = logging.getLogger(__name__)


class WsServer:
    """Lightweight WebSocket broadcast server."""

    def __init__(self, manager: MemorySyncManager,
                 host: str = "0.0.0.0", port: int = 8765):
        self._manager = manager
        self._host = host
        self._port = port
        self._clients: set = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._server = None

    def start(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run, daemon=True
        )
        self._thread.start()

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        try:
            import websockets
        except ImportError:
            logger.error("websockets package not installed")
            return
        start_server = websockets.serve(
            self._handler, self._host, self._port, loop=self._loop
        )
        self._server = self._loop.run_until_complete(start_server)
        self._loop.run_forever()

    async def _handler(self, websocket, path):
        self._clients.add(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    from stellar_memory.models import ChangeEvent
                    evt = ChangeEvent.from_dict(data)
                    if self._manager.apply_remote(evt):
                        await self._broadcast(message, exclude=websocket)
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning("Invalid sync message: %s", e)
        except Exception:
            pass
        finally:
            self._clients.discard(websocket)

    async def _broadcast(self, message: str, exclude=None) -> None:
        for client in list(self._clients):
            if client is not exclude:
                try:
                    await client.send(message)
                except Exception:
                    self._clients.discard(client)

    def broadcast_event(self, event) -> None:
        """Send event to all connected clients (from main thread)."""
        if not self._loop or not self._clients:
            return
        msg = json.dumps(event.to_dict())
        asyncio.run_coroutine_threadsafe(
            self._broadcast(msg), self._loop
        )

    def stop(self) -> None:
        if self._server:
            self._server.close()
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=2)
