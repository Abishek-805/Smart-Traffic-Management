"""
ConnectionManager handles active WebSocket connections for camera nodes.
"""

import asyncio
from dataclasses import dataclass
import uuid
from typing import Dict, Optional
from fastapi import WebSocket
from ai.utils.logger import get_logger

logger = get_logger("ConnectionManager")


@dataclass(frozen=True)
class ConnectionLease:
    """Ownership identity for one node's current WebSocket generation."""

    node_id: str
    generation: str
    websocket: WebSocket


class ConnectionManager:
    """
    Manages active WebSocket connections for camera nodes.
    Supports node registration, graceful disconnection, messaging, and broadcasting.
    """

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_leases: Dict[str, ConnectionLease] = {}

    async def connect(
        self,
        node_id: str,
        websocket: WebSocket,
        generation: Optional[str] = None,
    ) -> ConnectionLease:
        """
        Register a WebSocket connection for a node.
        If node_id is already connected (reconnect scenario), replaces existing connection.
        """
        if node_id in self.active_connections:
            logger.warning(f"Reconnection for node '{node_id}'. Replacing active WebSocket connection.")
            old_ws = self.active_connections.pop(node_id)
            try:
                await old_ws.close(code=1000, reason="Replaced by new connection")
            except Exception:
                pass

        lease = ConnectionLease(
            node_id=node_id,
            generation=generation or uuid.uuid4().hex,
            websocket=websocket,
        )
        self.active_connections[node_id] = websocket
        self.connection_leases[node_id] = lease
        logger.info(f"WebSocket registered for node '{node_id}'. Total active connections: {len(self.active_connections)}")
        return lease

    async def disconnect(
        self,
        node_id: str,
        generation: Optional[str] = None,
        websocket: Optional[WebSocket] = None,
    ) -> bool:
        """Disconnect only the current matching node ownership generation."""
        lease = self.connection_leases.get(node_id)
        current = self.active_connections.get(node_id)
        if current is None:
            return False
        if lease is not None and generation is not None and lease.generation != generation:
            return False
        if websocket is not None and current is not websocket:
            return False

        ws = self.active_connections.pop(node_id, None)
        self.connection_leases.pop(node_id, None)
        if ws:
            try:
                await asyncio.wait_for(ws.close(code=1000), timeout=2)
            except Exception:
                pass
            logger.info(f"WebSocket unregistered for node '{node_id}'. Active connections: {len(self.active_connections)}")
            return True
        return False

    async def send_json(self, data: dict, websocket: WebSocket) -> bool:
        """Send JSON payload directly to a WebSocket instance."""
        try:
            await asyncio.wait_for(websocket.send_json(data), timeout=2)
            return True
        except Exception as e:
            logger.error(f"Error sending JSON payload over WebSocket: {e}")
            return False

    async def send_to_node(self, node_id: str, data: dict) -> bool:
        """Send JSON payload to a specific node_id connection."""
        ws = self.active_connections.get(node_id)
        if not ws:
            logger.warning(f"Cannot send message: Node '{node_id}' is not connected.")
            return False
        return await self.send_json(data, ws)

    async def broadcast(self, data: dict) -> None:
        """Broadcast JSON payload to all active node WebSockets."""
        for node_id, ws in list(self.active_connections.items()):
            try:
                await asyncio.wait_for(ws.send_json(data), timeout=2)
            except Exception as e:
                logger.error(f"Error broadcasting to node '{node_id}': {e}")

    def get_connection(self, node_id: str) -> Optional[WebSocket]:
        """Retrieve active WebSocket for node_id."""
        return self.active_connections.get(node_id)
