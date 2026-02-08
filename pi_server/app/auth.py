from fastapi import Header, HTTPException
from typing import Optional
from .storage.device_store import DeviceStore

class ApiKeyAuth:
    def __init__(self, device_store: DeviceStore):
        self.device_store = device_store

    async def verify(self, device_id: str, x_api_key: Optional[str] = Header(None)) -> None:
        if not x_api_key:
            raise HTTPException(status_code=401, detail="Missing API key")
        record = await self.device_store.get_by_id(device_id)
        if not record or record["api_key"] != x_api_key:
            raise HTTPException(status_code=403, detail="Invalid API key")
