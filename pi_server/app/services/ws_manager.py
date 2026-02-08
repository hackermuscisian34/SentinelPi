import asyncio
from typing import Dict, Any
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self) -> None:
        self.active: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, device_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active[device_id] = websocket

    async def disconnect(self, device_id: str) -> None:
        async with self._lock:
            self.active.pop(device_id, None)

    async def send_command(self, device_id: str, payload: Dict[str, Any]) -> bool:
        ws = self.active.get(device_id)
        if not ws:
            return False
        await ws.send_json(payload)
        return True
