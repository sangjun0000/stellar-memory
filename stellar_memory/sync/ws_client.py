"""WebSocket client for connecting to a remote sync server."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.sync.sync_manager import MemorySyncManager

logger = logging.getLogger(__name__)


class WsClient:
    """Connects to a remote WsServer and exchanges ChangeEvents."""

    def __init__(self, manager: MemorySyncManager, url: str,
                 api_key: str | None = None):
        self._manager = manager
        self._url = url
        self._api_key = api_key
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._ws = None
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 30.0
        self._running = False

    def start(self) -> None:
        self._running = True
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run, daemon=True
        )
        self._thread.start()

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._run_with_reconnect())

    async def _run_with_reconnect(self) -> None:
        try:
            import websockets
        except ImportError:
            logger.error("websockets package not installed")
            return
        while self._running:
            try:
                async with websockets.connect(self._url) as ws:
                    self._ws = ws
                    self._reconnect_delay = 1.0
                    # Authenticate if api_key is provided
                    if self._api_key:
                        await ws.send(json.dumps({"api_key": self._api_key}))
                        resp = json.loads(await ws.recv())
                        if not resp.get("authenticated"):
                            raise ConnectionError("WebSocket auth failed")
                    # send pending events
                    for evt in self._manager.flush_pending():
                        await ws.send(json.dumps(evt.to_dict()))
                    # receive loop
                    async for message in ws:
                        try:
                            data = json.loads(message)
                            from stellar_memory.models import ChangeEvent
                            evt = ChangeEvent.from_dict(data)
                            self._manager.apply_remote(evt)
                        except (json.JSONDecodeError, KeyError) as e:
                            logger.warning("Invalid message: %s", e)
            except Exception as e:
                self._ws = None
                if not self._running:
                    break
                logger.warning(
                    "Sync client connection failed: %s (retry in %.0fs)",
                    e, self._reconnect_delay
                )
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2, self._max_reconnect_delay
                )

    def send_event(self, event) -> None:
        if not self._loop or not self._ws:
            return
        msg = json.dumps(event.to_dict())
        asyncio.run_coroutine_threadsafe(
            self._ws.send(msg), self._loop
        )

    def stop(self) -> None:
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=2)
