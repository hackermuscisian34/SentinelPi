import asyncio
import json
import logging
import threading
import uuid
import paho.mqtt.client as mqtt
from typing import Callable, Any, Optional
from ..config import settings

logger = logging.getLogger("mqtt")

class MQTTService:
    def __init__(self, telemetry_buffer, detection_engine):
        self.client = mqtt.Client()
        self.telemetry_buffer = telemetry_buffer
        self.detection_engine = detection_engine
        self._pending: dict[str, dict] = {}  # correlation_id -> {event, result}

        # Callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT Broker!")
            # Subscribe to all device telemetry, heartbeats, and responses
            client.subscribe("sentinel/telemetry/#")
            client.subscribe("sentinel/heartbeat/#")
            client.subscribe("sentinelpi/response/#")  # For sync command responses
        else:
            logger.error(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())

            if topic.startswith("sentinelpi/response/"):
                # sentinelpi/response/{device_id}/{correlation_id}
                parts = topic.split("/")
                if len(parts) >= 4:
                    correlation_id = parts[-1]
                    if correlation_id in self._pending:
                        self._pending[correlation_id]["result"] = payload
                        self._pending[correlation_id]["event"].set()
            elif topic.startswith("sentinel/telemetry/"):
                device_id = topic.split("/")[-1]
                asyncio.run_coroutine_threadsafe(
                    self.process_telemetry(device_id, payload),
                    asyncio.get_event_loop()
                )
            elif topic.startswith("sentinel/heartbeat/"):
                pass

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def on_disconnect(self, client, userdata, rc):
        logger.warning(f"Disconnected from MQTT Broker (rc={rc})")

    async def process_telemetry(self, device_id: str, payload: dict):
        try:
            await self.telemetry_buffer.add(device_id, json.dumps(payload))
        except Exception as e:
            logger.error(f"Failed to buffer telemetry: {e}")

    def start(self):
        try:
            self.client.connect("localhost", 1883, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def publish_command(self, device_id: str, command: str, args: dict = None):
        topic = f"sentinel/command/{device_id}"
        payload = json.dumps({"command": command, "args": args or {}})
        info = self.client.publish(topic, payload, qos=1)
        return info.rc == mqtt.MQTT_ERR_SUCCESS

    def publish_command_sync(
        self, device_id: str, command: str, args: dict = None, timeout: float = 15.0
    ) -> Optional[dict]:
        """Publish a command and wait for the agent's response. Returns the result dict or None on timeout."""
        correlation_id = str(uuid.uuid4())
        event = threading.Event()
        self._pending[correlation_id] = {"event": event, "result": None}

        topic = f"sentinel/command/{device_id}"
        payload = json.dumps({
            "command": command,
            "args": args or {},
            "correlation_id": correlation_id,
        })
        info = self.client.publish(topic, payload, qos=1)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            del self._pending[correlation_id]
            return None

        triggered = event.wait(timeout=timeout)
        result = self._pending.pop(correlation_id, {}).get("result")
        return result if triggered else None

