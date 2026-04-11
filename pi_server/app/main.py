import json
import uuid
import asyncio
from datetime import datetime
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .config import settings
from .utils.logging import setup_logging
from .schemas.models import CommandResponse
from .services.pairing import PairingManager
from .services.detection import DetectionEngine
from .services.ws_manager import ConnectionManager
from .services.mqtt_service import MQTTService
from .storage.telemetry_buffer import TelemetryBuffer

from .storage.device_store import DeviceStore
from .supabase_client import SupabaseClient
from .auth import ApiKeyAuth
import httpx
from .routes.health import build_health_router
from .routes.pairing import build_pairing_router
from .routes.agent import build_agent_router
from .routes.command import build_command_router
from .services.ml_service import MLService

setup_logging()

app = FastAPI(title="SentinelPi-EDR", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pairing_manager = PairingManager()
telemetry_buffer = TelemetryBuffer(settings.telemetry_buffer_db_path)
device_store = DeviceStore(settings.telemetry_buffer_db_path)
ws_manager = ConnectionManager()
detection_engine = DetectionEngine()
ml_service = MLService()
mqtt_service = MQTTService(telemetry_buffer, detection_engine)
supabase = SupabaseClient()

auth = ApiKeyAuth(device_store)

async def verify_supabase_jwt(authorization: str | None = Header(None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": settings.supabase_anon_key,
                },
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            return resp.json()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

@app.on_event("startup")
async def startup() -> None:
    print(f"DEBUG: DeviceStore.delete exists: {hasattr(device_store, 'delete')}")
    os.makedirs(os.path.dirname(settings.telemetry_buffer_db_path), exist_ok=True)
    await telemetry_buffer.init()
    await device_store.init()
    mqtt_service.start()
    asyncio.create_task(flush_telemetry_loop())

@app.on_event("shutdown")
async def shutdown() -> None:
    mqtt_service.stop()
    await supabase.close()


async def send_alerts(device_id: str, alerts: list[dict]) -> None:
    import logging
    _log = logging.getLogger("send_alerts")
    rows = []
    for alert in alerts:
        rows.append(
            {
                "device_id": device_id,
                "timestamp": alert.get("timestamp"),
                "severity": alert.get("severity"),
                "title": alert.get("title"),
                "description": alert.get("description"),
                "metadata": json.dumps(alert.get("metadata", {})),
            }
        )
    try:
        await supabase.insert("alerts", rows)
        _log.info(f"Inserted {len(rows)} alert(s) for device {device_id} into Supabase.")
    except Exception as e:
        _log.error(f"FAILED to insert alerts into Supabase for device {device_id}: {e}")
        raise  # Re-raise so the caller can return HTTP 500 instead of silently dropping

app.include_router(build_health_router())
app.include_router(build_pairing_router(pairing_manager, device_store, supabase, verify_supabase_jwt))
app.include_router(build_agent_router(telemetry_buffer, detection_engine, auth, send_alerts, ml_service))
app.include_router(build_command_router(mqtt_service, supabase, verify_supabase_jwt))


@app.websocket("/ws/agent/{device_id}")
async def ws_agent(websocket: WebSocket, device_id: str, api_key: str | None = None):
    if not api_key:
        await websocket.close(code=1008)
        return
    record = await device_store.get_by_id(device_id)
    if not record or record["api_key"] != api_key:
        await websocket.close(code=1008)
        return

    await ws_manager.connect(device_id, websocket)
    try:
        while True:
            msg = await websocket.receive_json()
            if msg.get("type") == "heartbeat":
                await websocket.send_json({"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()})
            elif msg.get("type") == "telemetry":
                await telemetry_buffer.add(device_id, json.dumps(msg.get("payload")))
    except WebSocketDisconnect:
        await ws_manager.disconnect(device_id)

async def flush_telemetry_loop() -> None:
    import logging
    logger = logging.getLogger("telemetry_flush")
    
    while True:
        await asyncio.sleep(settings.telemetry_flush_interval_seconds)
        batch = await telemetry_buffer.fetch_batch(limit=100)
        if not batch:
            continue
        ids = [b["id"] for b in batch]
        try:
            rows = []
            for item in batch:
                payload = json.loads(item["payload"])
                rows.append(
                    {
                        "device_id": payload.get("device_id"),
                        "timestamp": payload.get("timestamp"),
                        "summary": {
                                "cpu": payload.get("cpu"),
                                "memory": payload.get("memory"),
                                "process_count": len(payload.get("processes", [])),
                            },
                    }
                )
            # Use the custom wrapper's insert method: insert(table, rows)
            await supabase.insert("telemetry_summaries", rows)
            await telemetry_buffer.delete_ids(ids)
        except Exception as e:
            # Log detailed error information
            error_msg = str(e)
            logger.error(f"Flush error: {e}")
            
            # If it's a foreign key violation, log which device_id is problematic
            if "23503" in error_msg or "foreign key constraint" in error_msg.lower():
                device_ids = [json.loads(item["payload"]).get("device_id") for item in batch]
                logger.error(f"Foreign key violation for device_id(s): {set(device_ids)}")
                logger.error("These devices may not exist in the 'devices' table in Supabase")
            
            continue


@app.delete("/devices/{device_id}", response_model=CommandResponse)
async def delete_device(device_id: str, user=Depends(verify_supabase_jwt)):
    try:
        print(f"DEBUG: Attempting to delete device {device_id}")
        # Remove from local store
        if hasattr(device_store, 'delete'):
             await device_store.delete(device_id)
        else:
             print("ERROR: DeviceStore missing delete method!")
             raise Exception("Server code outdated: DeviceStore.delete missing")

        # Remove from Supabase
        print(f"DEBUG: Deleting from Supabase...")
        # Use custom wrapper's delete method: delete(table, match)
        await supabase.delete("devices", {"device_id": device_id})
        print(f"DEBUG: Device {device_id} deleted successfully.")
        return CommandResponse(status="ok", message="Device removed")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR in delete_device: {e}")
        raise HTTPException(status_code=500, detail=str(e))
