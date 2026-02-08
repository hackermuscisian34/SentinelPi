import aiosqlite
import asyncio
from typing import Dict, Any, Optional, List

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    api_key TEXT NOT NULL,
    device_hostname TEXT NOT NULL,
    agent_version TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

class DeviceStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = asyncio.Lock()

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(CREATE_TABLE_SQL)
            await db.commit()

    async def add(self, device: Dict[str, Any]) -> None:
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO devices (device_id, api_key, device_hostname, agent_version, created_at) VALUES (?, ?, ?, ?, ?)",
                    (
                        device["device_id"],
                        device["api_key"],
                        device["device_hostname"],
                        device["agent_version"],
                        device["created_at"],
                    ),
                )
                await db.commit()

    async def get_by_id(self, device_id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT device_id, api_key, device_hostname, agent_version, created_at FROM devices WHERE device_id=?",
                (device_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            return {
                "device_id": row[0],
                "api_key": row[1],
                "device_hostname": row[2],
                "agent_version": row[3],
                "created_at": row[4],
            }

    async def list_all(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT device_id, api_key, device_hostname, agent_version, created_at FROM devices"
            )
            rows = await cursor.fetchall()
            return [
                {
                    "device_id": r[0],
                    "api_key": r[1],
                    "device_hostname": r[2],
                    "agent_version": r[3],
                    "created_at": r[4],
                }
                for r in rows
            ]
