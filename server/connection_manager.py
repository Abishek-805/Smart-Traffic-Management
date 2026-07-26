"""
ConnectionManager handles active WebSocket connections for camera nodes.
"""

from typing import Dict, Optional
from fastapi import WebSocket
from ai.utils.logger import get_logger

logger = get_logger("ConnectionManager")


class ConnectionManager:
    """
    Manages active WebSocket connections for camera nodes.
    Supports node registration, graceful disconnection, messaging, and broadcasting.
    """

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, node_id: str, websocket: WebSocket) -> None:
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

        self.active_connections[node_id] = websocket
        logger.info(f"WebSocket registered for node '{node_id}'. Total active connections: {len(self.active_connections)}")

    async def disconnect(self, node_id: str) -> None:
        """Disconnect and unregister node WebSocket."""
        ws = self.active_connections.pop(node_id, None)
        if ws:
            logger.info(f"WebSocket unregistered for node '{node_id}'. Active connections: {len(self.active_connections)}")

    async def send_json(self, data: dict, websocket: WebSocket) -> bool:
        """Send JSON payload directly to a WebSocket instance."""
        try:
            await websocket.send_json(data)
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
                await ws.send_json(data)
            except Exception as e:
                logger.error(f"Error broadcasting to node '{node_id}': {e}")

    def get_connection(self, node_id: str) -> Optional[WebSocket]:
        """Retrieve active WebSocket for node_id."""
        return self.active_connections.get(node_id)
