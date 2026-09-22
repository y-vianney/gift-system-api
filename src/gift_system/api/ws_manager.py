from __future__ import annotations

import json
from typing import Any
from fastapi import WebSocket


class ThreadConnectionManager:
    """Manages active, in-memory WebSocket connections per letterbox thread."""

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, thread_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if thread_id not in self._connections:
            self._connections[thread_id] = []
        self._connections[thread_id].append(websocket)

    def disconnect(self, thread_id: str, websocket: WebSocket) -> None:
        if thread_id in self._connections:
            if websocket in self._connections[thread_id]:
                self._connections[thread_id].remove(websocket)
            if not self._connections[thread_id]:
                del self._connections[thread_id]

    async def broadcast(self, thread_id: str, message: dict[str, Any]) -> None:
        """Broadcast a message payload to all clients connected to thread_id."""
        if thread_id not in self._connections:
            return

        dead_sockets: list[WebSocket] = []
        payload_text = json.dumps(message)

        for ws in self._connections[thread_id]:
            try:
                await ws.send_text(payload_text)
            except Exception:
                dead_sockets.append(ws)

        for ws in dead_sockets:
            self.disconnect(thread_id, ws)


ws_manager = ThreadConnectionManager()
