from fastapi import WebSocket
from collections import defaultdict

class ConnectionManager:
    def __init__(self):
        self.connections = defaultdict(list)

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.connections[user_id].append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        if websocket in self.connections[user_id]:
            self.connections[user_id].remove(websocket)

        if not self.connections[user_id]:
            del self.connections[user_id]

    async def send_to_user(self, user_id: int, data: dict):
        for ws in self.connections.get(user_id, []):
            await ws.send_json(data)

    async def send_notification(self, user_id: int, data: dict):
        for ws in self.connections.get(user_id, []):
            await ws.send_json(data)

manager = ConnectionManager()