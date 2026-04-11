import asyncio
import json
import threading
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from ..schemas.models import CommandRequest, CommandResponse


def build_command_router(mqtt_service, supabase, verify_supabase_jwt) -> APIRouter:

    router = APIRouter()

    @router.post("/command", response_model=CommandResponse)
    async def send_command(payload: CommandRequest, user=Depends(verify_supabase_jwt)) -> CommandResponse:
        delivered = mqtt_service.publish_command(
            payload.device_id, payload.command, payload.args
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

    @router.post("/command/sync")
    async def send_command_sync(payload: CommandRequest, user=Depends(verify_supabase_jwt)):
        """
        Send a command and wait up to 15 s for the agent to reply.
        Implements the request/response pattern inline so that no changes
        to mqtt_service.py are required.
        """
        correlation_id = str(uuid.uuid4())
        event = threading.Event()
        result_holder: dict = {}

        response_topic = f"sentinelpi/response/{payload.device_id}/{correlation_id}"

        def on_response(client, userdata, msg):
            try:
                if msg.topic == response_topic:
                    result_holder["result"] = json.loads(msg.payload.decode())
                    event.set()
            except Exception:
                pass

        # Subscribe to the per-request response topic
        mqtt_service.client.subscribe(response_topic)
        mqtt_service.client.message_callback_add(response_topic, on_response)

        try:
            # Publish command with correlation_id so the agent knows where to reply
            cmd_payload = json.dumps({
                "command": payload.command,
                "args": payload.args or {},
                "correlation_id": correlation_id,
            })
            topic = f"sentinel/command/{payload.device_id}"
            info = mqtt_service.client.publish(topic, cmd_payload, qos=1)
            if info.rc != 0:
                raise HTTPException(status_code=502, detail="Failed to publish command to MQTT broker")

            # Wait in a thread executor so we don't block the event loop
            loop = asyncio.get_event_loop()
            triggered = await loop.run_in_executor(None, lambda: event.wait(15.0))

            if not triggered or "result" not in result_holder:
                raise HTTPException(
                    status_code=504,
                    detail="Agent did not respond in time. Make sure the agent is running.",
                )

            return result_holder["result"]

        finally:
            mqtt_service.client.message_callback_remove(response_topic)
            mqtt_service.client.unsubscribe(response_topic)

    return router
