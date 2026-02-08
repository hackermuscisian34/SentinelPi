import asyncio
import json
import logging
import socket
import requests
import websockets
from typing import Optional
from .config import config
from .services.credentials import CredentialStore
from .services.telemetry import TelemetryCollector
from .services.commands import CommandExecutor

logger = logging.getLogger("agent")

class AgentClient:
    def __init__(self) -> None:
        self.creds = CredentialStore()
        self.telemetry = TelemetryCollector()
        self.commands = CommandExecutor()
        self._stop_event = asyncio.Event()

    def enrolled(self) -> bool:
        return bool(self.creds.get("device_id") and self.creds.get("api_key"))

    def enroll(self, pi_ip: str, pairing_code: str) -> dict:
        hostname = socket.gethostname() if config.DEVICE_HOSTNAME == "AUTO" else config.DEVICE_HOSTNAME
        payload = {
            "pairing_code": pairing_code,
            "device_hostname": hostname,
            "agent_version": config.AGENT_VERSION,
        }
        resp = requests.post(f"http://{pi_ip}:{config.PI_SERVER_PORT}/enroll", json=payload, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"Enrollment failed: {resp.status_code} {resp.text}")
        data = resp.json()
        self.creds.set("device_id", data["device_id"])
        self.creds.set("api_key", data["api_key"])
        self.creds.set("pi_ip", pi_ip)
        return data

    async def start(self) -> None:
        if not self.enrolled():
            logger.error("Agent not enrolled")
            return
        await asyncio.gather(self._telemetry_loop(), self._ws_loop())

    async def stop(self) -> None:
        self._stop_event.set()

    async def _telemetry_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await asyncio.sleep(config.TELEMETRY_INTERVAL_SECONDS)
                payload = self.telemetry.collect()
                device_id = self.creds.get("device_id")
                api_key = self.creds.get("api_key")
                pi_ip = self.creds.get("pi_ip") or config.PI_SERVER_IP
                payload["device_id"] = device_id
                resp = requests.post(
                    f"http://{pi_ip}:{config.PI_SERVER_PORT}/telemetry",
                    json=payload,
                    headers={"X-API-Key": api_key},
                    timeout=10,
                )
                if resp.status_code != 200:
                    logger.warning("Telemetry failed: %s", resp.text)
            except Exception as exc:
                logger.warning("Telemetry error: %s", exc)

    async def _ws_loop(self) -> None:
        attempts = 0
        while not self._stop_event.is_set():
            device_id = self.creds.get("device_id")
            api_key = self.creds.get("api_key")
            pi_ip = self.creds.get("pi_ip") or config.PI_SERVER_IP
            ws_url = f"ws://{pi_ip}:{config.PI_SERVER_WEBSOCKET_PORT}/ws/agent/{device_id}?api_key={api_key}"
            try:
                async with websockets.connect(ws_url, ping_interval=None) as ws:
                    attempts = 0
                    await self._heartbeat_loop(ws)
            except Exception as exc:
                attempts += 1
                if config.MAX_RECONNECT_ATTEMPTS and attempts >= config.MAX_RECONNECT_ATTEMPTS:
                    logger.error("Max reconnect attempts reached")
                    return
                await asyncio.sleep(config.RECONNECT_INTERVAL_SECONDS)

    async def _heartbeat_loop(self, ws) -> None:
        while not self._stop_event.is_set():
            await ws.send(json.dumps({"type": "heartbeat"}))
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=config.HEARTBEAT_INTERVAL_SECONDS)
                data = json.loads(msg)
                if data.get("command"):
                    result = self.commands.execute(data["command"], data.get("args", {}))
                    await self._send_command_result(data["command"], result)
            except asyncio.TimeoutError:
                continue
            except Exception as exc:
                logger.warning("WS error: %s", exc)
                break

    async def _send_command_result(self, command: str, result: dict) -> None:
        device_id = self.creds.get("device_id")
        api_key = self.creds.get("api_key")
        pi_ip = self.creds.get("pi_ip") or config.PI_SERVER_IP
        payload = {
            "device_id": device_id,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "severity": "info" if result.get("status") == "ok" else "medium",
            "title": f"Command {command}",
            "description": json.dumps(result),
            "metadata": result,
        }
        try:
            requests.post(
                f"http://{pi_ip}:{config.PI_SERVER_PORT}/alert",
                json=payload,
                headers={"X-API-Key": api_key},
                timeout=10,
            )
        except Exception:
            pass
