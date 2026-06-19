"""WebSocket connection manager with pub/sub channels."""

import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections with channel-based pub/sub.

    Channels:
    - chat:{customer_id} — Customer chat messages
    - admin — All admin dashboard events (broadcast)
    """

    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        """Accept and register a WebSocket connection on a channel."""
        await websocket.accept()
        async with self._lock:
            if channel not in self._connections:
                self._connections[channel] = set()
            self._connections[channel].add(websocket)

    async def disconnect(self, websocket: WebSocket, channel: str) -> None:
        """Remove a WebSocket connection from a channel."""
        async with self._lock:
            if channel in self._connections:
                self._connections[channel].discard(websocket)
                if not self._connections[channel]:
                    del self._connections[channel]

    async def broadcast(self, channel: str, message: dict) -> None:
        """Broadcast a message to all connections on a channel."""
        async with self._lock:
            connections = list(self._connections.get(channel, set()))

        dead_connections = []
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead_connections.append(ws)

        # Clean up dead connections
        if dead_connections:
            async with self._lock:
                for ws in dead_connections:
                    if channel in self._connections:
                        self._connections[channel].discard(ws)

    async def send_personal(self, websocket: WebSocket, message: dict) -> None:
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            pass

    @property
    def active_connections_count(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


# Global connection manager singleton
manager = ConnectionManager()
