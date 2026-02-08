import aiosqlite
import asyncio
from typing import List, Dict, Any
from datetime import datetime

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

class TelemetryBuffer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = asyncio.Lock()

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(CREATE_TABLE_SQL)
            await db.commit()

    async def add(self, device_id: str, payload: str) -> None:
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO telemetry (device_id, payload, created_at) VALUES (?, ?, ?)",
                    (device_id, payload, datetime.utcnow().isoformat()),
                )
                await db.commit()

    async def fetch_batch(self, limit: int = 100) -> List[Dict[str, Any]]:
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT id, device_id, payload, created_at FROM telemetry ORDER BY id ASC LIMIT ?",
                    (limit,),
                )
                rows = await cursor.fetchall()
                return [
                    {"id": r[0], "device_id": r[1], "payload": r[2], "created_at": r[3]}
                    for r in rows
                ]

    async def delete_ids(self, ids: List[int]) -> None:
        if not ids:
            return
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                q = "DELETE FROM telemetry WHERE id IN ({})".format(
                    ",".join(["?"] * len(ids))
                )
                await db.execute(q, ids)
                await db.commit()
