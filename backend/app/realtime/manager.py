"""WebSocket connection manager for real-time telemetry streaming."""
from typing import Dict, List
from fastapi import WebSocket
from app.core.logging import logger
from app.realtime.events import RealtimeEvent


class ConnectionManager:
    """Manages active WebSocket connections subscribed to device data streams."""

    def __init__(self):
        # Maps device_id -> List of WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, device_id: str):
        await websocket.accept()
        if device_id not in self.active_connections:
            self.active_connections[device_id] = []
        self.active_connections[device_id].append(websocket)
        logger.info(f"WebSocket client connected to device stream '{device_id}'")

    def disconnect(self, websocket: WebSocket, device_id: str):
        if device_id in self.active_connections:
            if websocket in self.active_connections[device_id]:
                self.active_connections[device_id].remove(websocket)
            if not self.active_connections[device_id]:
                del self.active_connections[device_id]
        logger.info(f"WebSocket client disconnected from stream '{device_id}'")

    async def broadcast(self, device_id: str, event: RealtimeEvent):
        """Broadcasts an event to all subscribers of a specific device."""
        if device_id in self.active_connections:
            data = event.model_dump_json()
            for connection in self.active_connections[device_id]:
                try:
                    await connection.send_text(data)
                except Exception as exc:
                    logger.debug(f"Failed to send to client on {device_id}: {exc}")


ws_manager = ConnectionManager()
