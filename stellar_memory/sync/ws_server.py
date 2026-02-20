"""WebSocket server for memory sync with tenant isolation."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import threading
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.sync.sync_manager import MemorySyncManager

logger = logging.getLogger(__name__)


class WsServer:
    """WebSocket server with room-based tenant isolation."""

    def __init__(self, manager: MemorySyncManager,
                 host: str = "0.0.0.0", port: int = 8765,
                 auth_manager=None):
        self._manager = manager
        self._host = host
        self._port = port
        self._rooms: dict[str, set] = defaultdict(set)
        self._client_user: dict = {}
        self._auth_manager = auth_manager
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
        # Authenticate if auth_manager is available
        user_id = await self._authenticate(websocket)
        if self._auth_manager and not user_id:
            try:
                await websocket.close(1008, "Authentication required")
            except Exception:
                pass
            return

        # Use a default room for unauthenticated local mode
        room_id = user_id or "__local__"
        self._rooms[room_id].add(websocket)
        self._client_user[websocket] = room_id

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    from stellar_memory.models import ChangeEvent
                    evt = ChangeEvent.from_dict(data)
                    if self._manager.apply_remote(evt):
                        await self._broadcast_to_room(
                            room_id, message, exclude=websocket
                        )
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning("Invalid sync message: %s", e)
        except Exception:
            pass
        finally:
            self._rooms.get(room_id, set()).discard(websocket)
            self._client_user.pop(websocket, None)

    async def _authenticate(self, websocket) -> str | None:
        """Authenticate via first message containing api_key."""
        if not self._auth_manager:
            return None
        try:
            msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(msg)
            api_key = data.get("api_key", "")
            if api_key:
                key_hash = hashlib.sha256(api_key.encode()).hexdigest()
                user = await self._auth_manager.get_user_by_api_key(key_hash)
                if user:
                    await websocket.send(json.dumps({"authenticated": True}))
                    return user.id
            await websocket.send(json.dumps({"authenticated": False}))
        except Exception:
            pass
        return None

    async def _broadcast_to_room(self, room_id: str, message: str,
                                  exclude=None) -> None:
        """Broadcast to clients in the same room only."""
        for client in list(self._rooms.get(room_id, [])):
            if client is not exclude:
                try:
                    await client.send(message)
                except Exception:
                    self._rooms[room_id].discard(client)

    def broadcast_event(self, event, user_id: str | None = None) -> None:
        """Send event to clients (from main thread)."""
        if not self._loop:
            return
        msg = json.dumps(event.to_dict())
        room_id = user_id or "__local__"
        if self._rooms.get(room_id):
            asyncio.run_coroutine_threadsafe(
                self._broadcast_to_room(room_id, msg), self._loop
            )

    def stop(self) -> None:
        if self._server:
            self._server.close()
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=2)
