import httpx
import asyncio
from typing import Any, Dict, List
from .config import settings

class SupabaseClient:
    def __init__(self) -> None:
        self.base_url = settings.supabase_url.rstrip("/")
        self.service_key = settings.supabase_service_role_key
        self.anon_key = settings.supabase_anon_key
        self._client = httpx.AsyncClient(timeout=10.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(self, method: str, path: str, json: Dict[str, Any] | None = None) -> httpx.Response:
        headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}{path}"
        last_exc: Exception | None = None
        for attempt in range(1, 4):
            try:
                resp = await self._client.request(method, url, headers=headers, json=json)
                if resp.status_code >= 500:
                    await asyncio.sleep(0.5 * attempt)
                    continue
                return resp
            except Exception as exc:
                last_exc = exc
                await asyncio.sleep(0.5 * attempt)
        if last_exc:
            raise last_exc
        raise RuntimeError("Supabase request failed")

    async def insert(self, table: str, rows: List[Dict[str, Any]]) -> None:
        resp = await self._request("POST", f"/rest/v1/{table}", json=rows)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Supabase insert failed: {resp.status_code} {resp.text}")

    async def update(self, table: str, values: Dict[str, Any], match: Dict[str, Any]) -> None:
        query = "&".join([f"{k}=eq.{v}" for k, v in match.items()])
        resp = await self._request("PATCH", f"/rest/v1/{table}?{query}", json=values)
        if resp.status_code not in (200, 204):
            raise RuntimeError(f"Supabase update failed: {resp.status_code} {resp.text}")
