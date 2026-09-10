from fastapi import WebSocket
from collections import defaultdict


class ConnectionManager:
    def __init__(self):
        # conversation_id -> list of active WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, conversation_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[conversation_id].append(websocket)

    def disconnect(self, conversation_id: str, websocket: WebSocket):
        if websocket in self.active_connections[conversation_id]:
            self.active_connections[conversation_id].remove(websocket)
        if not self.active_connections[conversation_id]:
            del self.active_connections[conversation_id]

    async def broadcast(self, conversation_id: str, message: dict, exclude: WebSocket | None = None):
        for connection in self.active_connections.get(conversation_id, []):
            if connection is not exclude:
                await connection.send_json(message)


manager = ConnectionManager()