import json
import uuid
import asyncio
from datetime import datetime
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .config import settings
from .utils.logging import setup_logging
from .schemas.models import (
    PairingCodeCreate,
    PairingCodeResponse,
    EnrollmentRequest,
    EnrollmentResponse,
    TelemetryPayload,
    AlertPayload,
    CommandRequest,
    CommandResponse,
    HealthResponse,
)
from .services.pairing import PairingManager
from .services.detection import DetectionEngine
from .services.ws_manager import ConnectionManager
from .storage.telemetry_buffer import TelemetryBuffer
from .storage.device_store import DeviceStore
from .supabase_client import SupabaseClient
from .auth import ApiKeyAuth
import httpx

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
    os.makedirs(os.path.dirname(settings.telemetry_buffer_db_path), exist_ok=True)
    await telemetry_buffer.init()
    await device_store.init()
    asyncio.create_task(flush_telemetry_loop())

@app.on_event("shutdown")
async def shutdown() -> None:
    await supabase.close()

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")

@app.post("/pairing", response_model=PairingCodeResponse)
async def create_pairing_code(payload: PairingCodeCreate, user=Depends(verify_supabase_jwt)):
    result = pairing_manager.create(payload.device_name)
    # store pairing code in Supabase
    try:
        await supabase.insert(
            "pairing_codes",
            [
                {
                    "pairing_code": result["pairing_code"],
                    "device_name": payload.device_name,
                    "expires_at": result["expires_at"],
                    "created_by": user.get("id"),
                }
            ],
        )
    except Exception:
        pass
    return PairingCodeResponse(**result)

@app.post("/enroll", response_model=EnrollmentResponse)
async def enroll(request: EnrollmentRequest, http_request: Request) -> EnrollmentResponse:
    entry = pairing_manager.verify(request.pairing_code)
    if not entry:
        raise HTTPException(status_code=400, detail="Invalid or expired pairing code")

    device_id = str(uuid.uuid4())
    api_key = uuid.uuid4().hex
    created_at = datetime.utcnow().isoformat()
    await device_store.add(
        {
            "device_id": device_id,
            "api_key": api_key,
            "device_hostname": request.device_hostname,
            "agent_version": request.agent_version,
            "created_at": created_at,
        }
    )
    pairing_manager.consume(request.pairing_code)

    # store device in Supabase
    try:
        await supabase.insert(
            "devices",
            [
                {
                    "device_id": device_id,
                    "device_hostname": request.device_hostname,
                    "agent_version": request.agent_version,
                    "status": "online",
                    "created_at": created_at,
                }
            ],
        )
    except Exception:
        pass

    host = http_request.headers.get("host") or f"{settings.host}:{settings.port}"
    return EnrollmentResponse(
        device_id=device_id,
        api_key=api_key,
        websocket_url=f"ws://{host}/ws/agent/{device_id}",
    )

@app.post("/telemetry", response_model=CommandResponse)
async def ingest_telemetry(payload: TelemetryPayload, x_api_key: str | None = Header(None)) -> CommandResponse:
    await auth.verify(payload.device_id, x_api_key)
    payload_dict = payload.dict()
    await telemetry_buffer.add(payload.device_id, json.dumps(payload_dict))

    alerts = await detection_engine.analyze_telemetry(payload_dict)
    if alerts:
        await send_alerts(payload.device_id, alerts)

    return CommandResponse(status="ok", message="Telemetry accepted")

@app.post("/alert", response_model=CommandResponse)
async def ingest_alert(payload: AlertPayload, x_api_key: str | None = Header(None)) -> CommandResponse:
    await auth.verify(payload.device_id, x_api_key)
    await send_alerts(payload.device_id, [payload.dict()])
    return CommandResponse(status="ok", message="Alert accepted")

@app.post("/command", response_model=CommandResponse)
async def send_command(payload: CommandRequest, user=Depends(verify_supabase_jwt)) -> CommandResponse:
    delivered = await ws_manager.send_command(
        payload.device_id, {"command": payload.command, "args": payload.args}
    )
    if not delivered:
        raise HTTPException(status_code=404, detail="Device not connected")
    try:
        await supabase.insert(
            "audit_logs",
            [
                {
                    "device_id": payload.device_id,
                    "action": payload.command,
                    "actor": user.get("id"),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ],
        )
    except Exception:
        pass
    return CommandResponse(status="ok", message="Command delivered")

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
                        "summary": json.dumps(
                            {
                                "cpu": payload.get("cpu"),
                                "memory": payload.get("memory"),
                                "process_count": len(payload.get("processes", [])),
                            }
                        ),
                    }
                )
            await supabase.insert("telemetry_summaries", rows)
            await telemetry_buffer.delete_ids(ids)
        except Exception:
            continue

async def send_alerts(device_id: str, alerts: list[dict]) -> None:
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
    except Exception:
        pass
