
from fastapi import APIRouter
from ..schemas.models import HealthResponse
import socket

def build_health_router() -> APIRouter:
    router = APIRouter()

    @router.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        hostname = socket.gethostname()
        if not hostname:
            hostname = "unknown"
        return HealthResponse(status="ok", hostname=hostname)

    return router
