import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request
from ..schemas.models import PairingCodeCreate, PairingCodeResponse, EnrollmentRequest, EnrollmentResponse

def build_pairing_router(pairing_manager, device_store, supabase, verify_supabase_jwt) -> APIRouter:
    router = APIRouter()

    @router.post("/pairing", response_model=PairingCodeResponse)
    async def create_pairing_code(payload: PairingCodeCreate, user=Depends(verify_supabase_jwt)):
        result = pairing_manager.create(payload.device_name)
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

    @router.post("/enroll", response_model=EnrollmentResponse)
    async def enroll(request: EnrollmentRequest, http_request: Request) -> EnrollmentResponse:
        entry = pairing_manager.verify(request.pairing_code)
        if not entry:
            raise HTTPException(status_code=400, detail="Invalid or expired pairing code")

        device_id = str(uuid.uuid4())
        api_key = uuid.uuid4().hex
        created_at = datetime.utcnow().isoformat()
        
        # First, add to local device store
        await device_store.add(
            {
                "device_id": device_id,
                "api_key": api_key,
                "device_hostname": request.device_hostname,
                "agent_version": request.agent_version,
                "created_at": created_at,
            }
        )
        
        # Then, try to add to Supabase - if this fails, rollback local store
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
        except Exception as e:
            # Rollback: remove from local device store
            import logging
            logger = logging.getLogger("pairing")
            logger.error(f"Failed to insert device {device_id} into Supabase: {e}")
            
            # Remove from local store
            if hasattr(device_store, 'delete'):
                await device_store.delete(device_id)
            
            # Don't consume the pairing code since enrollment failed
            raise HTTPException(
                status_code=503,
                detail=f"Failed to register device in database: {str(e)}"
            )
        
        # Only consume pairing code after successful enrollment
        pairing_manager.consume(request.pairing_code)

        host = http_request.headers.get("host")
        if not host:
            host = http_request.url.netloc
        return EnrollmentResponse(
            device_id=device_id,
            api_key=api_key,
            websocket_url=f"ws://{host}/ws/agent/{device_id}",
        )

    return router
