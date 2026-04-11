import json
import logging
from fastapi import APIRouter, Header, HTTPException
from ..schemas.models import TelemetryPayload, AlertPayload, CommandResponse

logger = logging.getLogger("agent_route")

def build_agent_router(telemetry_buffer, detection_engine, auth, send_alerts, ml_service) -> APIRouter:
    router = APIRouter()

    @router.post("/telemetry", response_model=CommandResponse)
    async def ingest_telemetry(payload: TelemetryPayload, x_api_key: str | None = Header(None)) -> CommandResponse:
        try:
            await auth.verify(payload.device_id, x_api_key)
        except HTTPException as e:
            logger.error(f"Telemetry auth failed for device {payload.device_id}: {e.detail}")
            raise
        payload_dict = payload.dict()
        await telemetry_buffer.add(payload.device_id, json.dumps(payload_dict))

        alerts = await detection_engine.analyze_telemetry(payload_dict)
        if alerts:
            await send_alerts(payload.device_id, alerts)

        return CommandResponse(status="ok", message="Telemetry accepted")

    @router.post("/alert", response_model=CommandResponse)
    async def ingest_alert(payload: AlertPayload, x_api_key: str | None = Header(None)) -> CommandResponse:
        try:
            await auth.verify(payload.device_id, x_api_key)
        except HTTPException as e:
            logger.error(f"Alert auth FAILED for device '{payload.device_id}' — {e.detail}. "
                         f"Is the agent re-enrolled? Restart the Pi server if the device_id is new.")
            raise

        alert_dict = payload.dict()

        # Generate ML Report
        try:
            report = await ml_service.generate_report(alert_dict)
            if report:
                if "metadata" not in alert_dict:
                    alert_dict["metadata"] = {}
                elif isinstance(alert_dict["metadata"], str):
                    try:
                        alert_dict["metadata"] = json.loads(alert_dict["metadata"])
                    except Exception:
                        alert_dict["metadata"] = {}
                alert_dict["metadata"]["report_html"] = report
        except Exception as e:
            logger.warning(f"ML report generation failed (non-fatal): {e}")

        try:
            await send_alerts(payload.device_id, [alert_dict])
            logger.info(f"Alert saved for device {payload.device_id}: {payload.title}")
        except Exception as e:
            logger.error(f"Failed to save alert to Supabase for device {payload.device_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to store alert: {e}")

        return CommandResponse(status="ok", message="Alert accepted")

    return router
