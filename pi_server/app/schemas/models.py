from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PairingCodeCreate(BaseModel):
    device_name: str = Field(min_length=2, max_length=128)

class PairingCodeResponse(BaseModel):
    pairing_code: str
    expires_at: str

class EnrollmentRequest(BaseModel):
    pairing_code: str = Field(min_length=6, max_length=12)
    device_hostname: str = Field(min_length=1, max_length=128)
    agent_version: str = Field(min_length=1, max_length=32)

class EnrollmentResponse(BaseModel):
    device_id: str
    api_key: str
    websocket_url: str

class TelemetryPayload(BaseModel):
    device_id: str
    timestamp: str
    cpu: Dict[str, Any]
    memory: Dict[str, Any]
    processes: List[Dict[str, Any]]
    network: List[Dict[str, Any]]
    logins: List[Dict[str, Any]]
    usb: List[Dict[str, Any]]

class AlertPayload(BaseModel):
    device_id: str
    timestamp: str
    severity: str
    title: str
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CommandRequest(BaseModel):
    device_id: str
    command: str
    args: Dict[str, Any] = Field(default_factory=dict)

class CommandResponse(BaseModel):
    status: str
    message: str

class HealthResponse(BaseModel):
    status: str
