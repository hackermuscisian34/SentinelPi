import asyncio
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self) -> None:
        self.active: Dict[str, WebSocket] = {}
        self.queue: Dict[str, list] = {}  # Store pending commands
        self._lock = asyncio.Lock()


    async def connect(self, device_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active[device_id] = websocket
            
            # Flush pending commands
            if device_id in self.queue:
                print(f"DEBUG: Flushing {len(self.queue[device_id])} queued commands to {device_id}")
                for payload in self.queue[device_id]:
                    try:
                        await websocket.send_json(payload)
                    except Exception as e:
                        print(f"Error flushing queue: {e}")
                # Clear queue after attempting flush
                del self.queue[device_id]


    async def disconnect(self, device_id: str) -> None:
        async with self._lock:
            self.active.pop(device_id, None)

    async def send_command(self, device_id: str, payload: Dict[str, Any]) -> bool:
        ws = self.active.get(device_id)
        if not ws:
            # Queue the command if device is offline
            print(f"DEBUG: Device {device_id} offline. Queuing command.")
            async with self._lock:
                if device_id not in self.queue:
                    self.queue[device_id] = []
                self.queue[device_id].append(payload)
            # Return True so the API doesn't error out (client receives "Accepted")
            return True
            
        try:
            await ws.send_json(payload)
            return True
        except (WebSocketDisconnect, RuntimeError, Exception) as e:
            print(f"DEBUG: Send failed ({e}). Queuing command.")
            # Connection died during send? Queue it.
            async with self._lock:
                 if device_id not in self.queue:
                    self.queue[device_id] = []
                 self.queue[device_id].append(payload)
            
            await self.disconnect(device_id)
            return True # Still return True because we queued it


