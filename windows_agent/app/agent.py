import asyncio
import json
import logging
import os
import socket
import requests
try:
    from websockets.exceptions import InvalidStatus
except ImportError:
    from websockets.exceptions import InvalidStatusCode as InvalidStatus
from typing import Optional
import time
import threading
import queue
import paho.mqtt.client as mqtt
from supabase import create_client, Client

from .config import config, MQTT_BROKER, MQTT_PORT, SUPABASE_URL, SUPABASE_KEY, DEVICE_ID
from .services.credentials import CredentialStore
from .services.telemetry import TelemetryCollector
from .services.commands import CommandExecutor
from .services.file_watcher import DownloadWatcher
from .services.activity_monitor import ActivityMonitor
from .services.device_monitor import DeviceMonitor
from .services.camera_monitor import CameraMonitor

logger = logging.getLogger("agent")

class AgentClient:
    def __init__(self) -> None:
        self.creds = CredentialStore()
        self.telemetry = TelemetryCollector() # Kept telemetry as it's used later
        self.command_queue = queue.Queue() # Added command_queue
        self.commands = CommandExecutor()
        self.download_watcher = DownloadWatcher(self._on_file_changed)
        self.activity_monitor = ActivityMonitor(
            self._on_user_activity, 
            idle_threshold_seconds=config.ACTIVITY_IDLE_THRESHOLD_SECONDS
        )
        self.device_monitor = DeviceMonitor(self._on_security_alert)
        self.camera_monitor = CameraMonitor(self._on_security_alert)
        self._stop_event = asyncio.Event()

        # Initialize Supabase
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # System Info
        self.hostname = socket.gethostname()
        self.ip_address = socket.gethostbyname(self.hostname)

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
        self._stop_event.clear()
        if not self.enrolled():
            logger.error("Agent not enrolled")
            return
        
        # Cache credentials
        self.device_id = self.creds.get("device_id")
        self.api_key = self.creds.get("api_key")
        self.pi_ip = self.creds.get("pi_ip") or config.PI_SERVER_IP
        
        # Capture the running loop for thread-safe calls from MQTT
        # Capture the running loop for thread-safe calls from MQTT
        self.loop = asyncio.get_running_loop()
        
        self.download_watcher.start()
        self.activity_monitor.start()
        self.device_monitor.start()
        self.camera_monitor.start()

        await asyncio.gather(self._telemetry_loop(), self._ws_loop())

    async def stop(self) -> None:
        self.download_watcher.stop()
        self.activity_monitor.stop()
        self.device_monitor.stop()
        self.camera_monitor.stop()
        self._stop_event.set()

    async def disconnect(self) -> None:
        """Stops the agent and clears credentials."""
        await self.stop()
        self.creds.clear("device_id")
        self.creds.clear("api_key")
        self.creds.clear("pi_ip")

    async def _telemetry_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await asyncio.sleep(config.TELEMETRY_INTERVAL_SECONDS)
                payload = self.telemetry.collect()
                payload["device_id"] = self.device_id
                
                # Use requests for now as it is synchronous and simple? 
                # Or better: publish via MQTT if client is available?
                # For now keeping legacy HTTP telemetry to minimize breakage, 
                # since MQTT Service on Pi defaults to buffering.
                
                resp = requests.post(
                    f"http://{self.pi_ip}:{config.PI_SERVER_PORT}/telemetry",
                    json=payload,
                    headers={"X-API-Key": self.api_key},
                    timeout=10,
                )
                if resp.status_code != 200:
                    logger.warning("Telemetry failed: %s", resp.text)
            except Exception as exc:
                logger.warning("Telemetry error: %s", exc)

    # MQTT Loop replacing WS Loop
    async def _ws_loop(self) -> None:
        """Main loop for MQTT connection."""
        import paho.mqtt.client as mqtt
        
        device_id = self.creds.get("device_id")
        pi_ip = self.creds.get("pi_ip") or config.PI_SERVER_IP
        
        client = mqtt.Client(client_id=f"agent_{device_id}")
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logger.info("MQTT Connected!")
                client.subscribe(f"sentinel/command/{device_id}")
            else:
                logger.error(f"MQTT Connect failed: {rc}")

        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                command = payload.get("command")
                args = payload.get("args", {})
                correlation_id = payload.get("correlation_id") # Added correlation_id
                
                logger.info(f"Received MQTT command: {command}")
                # Execute in thread to not block MQTT loop
                result = self.commands.execute(command, args) 
                
                # Special handling for path discovery - upload to Supabase
                if command == "discover_paths" and result.get("status") == "ok":
                    paths = result.get("paths", [])
                    device_id = self.device_id
                    
                    logging.info(f"Uploading {len(paths)} paths to Supabase for device {device_id}")
                    
                    # Clear old paths first (optional, or rely on upsert if we had unique keys, but simple delete is safer for clean slate)
                    try:
                        self.supabase.table("device_paths").delete().eq("device_id", device_id).execute()
                    except Exception as e:
                        logging.warning(f"Failed to clear old paths: {e}")

                    # Insert new paths
                    to_insert = []
                    for p in paths:
                        to_insert.append({
                            "device_id": device_id,
                            "path": p["path"],
                            "label": p["label"],
                            "is_directory": True
                        })
                    
                    if to_insert:
                        self.supabase.table("device_paths").insert(to_insert).execute()
                    
                    result["message"] = "Paths uploaded to Supabase"

                # Publish result back to MQTT
                if correlation_id: # Only publish if correlation_id is present
                    client.publish(
                        f"sentinelpi/response/{self.device_id}/{correlation_id}",
                        json.dumps(result)
                    )

                if hasattr(self, 'loop') and self.loop:
                    future = asyncio.run_coroutine_threadsafe(
                        self._send_command_result(command, result),
                        self.loop
                    )
                    # Optional: Check for exceptions in future
                    try:
                        future.result(timeout=5)
                    except Exception as err:
                        logger.error(f"Failed to send result: {err}")
                else:
                    logger.error("No event loop available to send result")
                    
            except Exception as e:
                logger.error(f"Error handling MQTT message: {e}")

        client.on_connect = on_connect
        client.on_message = on_message
        
        try:
            logger.info(f"Connecting to MQTT Broker at {pi_ip}:{config.MQTT_BROKER_PORT}")
            client.connect(pi_ip, config.MQTT_BROKER_PORT, 60)
            client.loop_start()
            
            # Keep the async task alive and send heartbeats
            while not self._stop_event.is_set():
                heartbeat = {
                    "type": "heartbeat",
                    "device_id": device_id,
                    "timestamp": __import__("datetime").datetime.utcnow().isoformat()
                }
                client.publish("sentinel/heartbeat", json.dumps(heartbeat))
                await asyncio.sleep(config.HEARTBEAT_INTERVAL_SECONDS)
                
            client.loop_stop()
            client.disconnect()
            
        except Exception as e:
            logger.error(f"MQTT Loop Critical Error: {e}")
            await asyncio.sleep(5)




    async def _send_command_result(self, command: str, result: dict) -> None:
        """Post meaningful scan-result alerts to the Pi Server. Ignores non-scan commands."""
        import datetime, re

        # Only create alerts for scan-like commands
        SCAN_COMMANDS = {"trigger_scan", "auto_scan", "quarantine"}
        if command not in SCAN_COMMANDS:
            return

        device_id = self.creds.get("device_id")
        api_key   = self.creds.get("api_key")
        pi_ip     = self.creds.get("pi_ip") or config.PI_SERVER_IP

        scan_status = result.get("status", "error")

        # If the entire scan command errored (not just ClamAV), send a scan-error alert
        if scan_status == "error":
            payload = {
                "device_id":   device_id,
                "timestamp":   datetime.datetime.utcnow().isoformat(),
                "severity":    "warning",
                "title":       "⚠️ Auto-Scan Warning",
                "description": f"File scan encountered an issue: {result.get('message', 'Unknown error')}",
                "metadata":    {"command": command, "error": result.get("message", "")},
            }
            try:
                r = requests.post(
                    f"http://{pi_ip}:{config.PI_SERVER_PORT}/alert",
                    json=payload, headers={"X-API-Key": api_key}, timeout=10,
                )
                logger.info(f"Scan-error alert POST → {r.status_code}")
            except Exception as exc:
                logger.warning("Failed to send scan-error alert: %s", exc)
            return

        device_id = self.creds.get("device_id")
        api_key   = self.creds.get("api_key")
        pi_ip     = self.creds.get("pi_ip") or config.PI_SERVER_IP

        # ── Summarise ClamAV output ───────────────────────────────────────────
        clamav_raw  = result.get("clamav", {}).get("output", "") if isinstance(result.get("clamav"), dict) else ""
        yara_raw    = result.get("yara",   {}).get("output", "") if isinstance(result.get("yara"),   dict) else ""

        # Count files scanned and threats
        scanned_match = re.search(r"Scanned files:\s*(\d+)", clamav_raw)
        infected_match = re.search(r"Infected files:\s*(\d+)", clamav_raw)
        files_scanned = int(scanned_match.group(1)) if scanned_match else None
        threats_found = int(infected_match.group(1)) if infected_match else 0

        # Collect threat lines (lines ending with FOUND)
        threat_lines = [l.strip() for l in clamav_raw.splitlines() if "FOUND" in l]
        yara_hits    = [l.strip() for l in yara_raw.splitlines() if l.strip() and "---" not in l]

        has_threat = bool(threat_lines or yara_hits or threats_found > 0)

        # ── Build human-readable description ────────────────────────────────
        if has_threat:
            title = "🔍 Scan Complete — Threats Detected"
            severity = "high"
            parts = [f"Security scan finished with {threats_found or len(threat_lines)} threat(s) found."]
            if files_scanned:
                parts.append(f"{files_scanned} files were scanned.")
            if threat_lines:
                parts.append("Threats:\n" + "\n".join(f"  • {t}" for t in threat_lines[:10]))
            if yara_hits:
                parts.append("YARA matches:\n" + "\n".join(f"  • {y}" for y in yara_hits[:10]))
            description = "\n".join(parts)
        else:
            title = "✅ Scan Complete — No Threats Found"
            severity = "info"
            scanned_str = f"{files_scanned} files" if files_scanned else "all files"
            description = (
                f"Scan finished. {scanned_str} scanned — no threats detected. "
                f"Your system appears clean."
            )

        # ── Metadata (used by ML service and AlertsScreen detail view) ───────
        metadata: dict = {}
        if clamav_raw:
            metadata["clamav"] = {"status": "ok", "output": clamav_raw}
        if yara_raw:
            metadata["yara"] = {"status": "ok", "output": yara_raw}
        metadata["threats_found"] = threats_found
        if files_scanned:
            metadata["files_scanned"] = files_scanned
        metadata["command"] = command

        payload = {
            "device_id":   device_id,
            "timestamp":   datetime.datetime.utcnow().isoformat(),
            "severity":    severity,
            "title":       title,
            "description": description,
            "metadata":    metadata,
        }
        try:
            r = requests.post(
                f"http://{pi_ip}:{config.PI_SERVER_PORT}/alert",
                json=payload,
                headers={"X-API-Key": api_key},
                timeout=10,
            )
            logger.info(f"Alert POST → {r.status_code}: {title!r}")
            if r.status_code not in (200, 201):
                logger.error(f"Pi server rejected alert: {r.status_code} {r.text[:200]}")
        except Exception as exc:
            logger.warning("Failed to send scan alert: %s", exc)



    def _on_file_changed(self, path: str) -> None:
        """Callback for file watcher when a new file is detected."""
        logger.info(f"New file detected: {path} - Triggering scan")
        try:
            # Wait for the file to be fully written (browser downloads fire the
            # event before the file handle is closed / rename is complete)
            import time
            max_wait = 10  # seconds
            waited = 0
            while waited < max_wait:
                if os.path.exists(path) and os.path.getsize(path) > 0:
                    break
                time.sleep(1)
                waited += 1

            if not os.path.exists(path):
                logger.warning(f"File gone before scan could start (temp file?): {path}")
                return

            # Extra 1s settle — lets the OS finish flushing the file
            time.sleep(1)

            result = self.commands.execute("trigger_scan", {"path": path})
            clamav_out = result.get("clamav", {}).get("output", "(empty)")
            logger.info(f"Scan result for {path}: status={result.get('status')} | clamav={clamav_out[:200]!r}")

            if hasattr(self, 'loop') and self.loop:
                future = asyncio.run_coroutine_threadsafe(
                    self._send_command_result("auto_scan", result),
                    self.loop
                )
                try:
                    future.result(timeout=15)
                    logger.info(f"Alert posted successfully for {path}")
                except Exception as err:
                    logger.error(f"Alert post failed for {path}: {err}")
        except Exception as e:
            logger.error(f"Error handling file change for {path}: {e}", exc_info=True)



    def _on_user_activity(self) -> None:
        """Callback when user becomes active after being idle."""
        logger.info("User activity detected - Sending Alert")
        if hasattr(self, "loop") and self.loop:
            asyncio.run_coroutine_threadsafe(
                self._send_security_alert(
                    title="👤 User Activity Detected",
                    description="User input was detected on the monitored device after an idle period.",
                    severity="info",
                ),
                self.loop,
            )


    def _on_security_alert(self, title: str, description: str, severity: str) -> None:
        """Shared callback for DeviceMonitor and CameraMonitor alerts."""
        logger.warning("Security alert: [%s] %s — %s", severity.upper(), title, description)
        result = {
            "status": severity,
            "message": description,
            "title": title,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }
        if hasattr(self, "loop") and self.loop:
            asyncio.run_coroutine_threadsafe(
                self._send_security_alert(title, description, severity),
                self.loop,
            )

    async def _send_security_alert(self, title: str, description: str, severity: str) -> None:
        """Send a security alert directly to the Pi Server's /alert endpoint."""
        device_id = self.creds.get("device_id")
        api_key = self.creds.get("api_key")
        pi_ip = self.creds.get("pi_ip") or config.PI_SERVER_IP
        import datetime
        payload = {
            "device_id": device_id,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "severity": severity,
            "title": title,
            "description": description,
            "metadata": {},
        }
        try:
            requests.post(
                f"http://{pi_ip}:{config.PI_SERVER_PORT}/alert",
                json=payload,
                headers={"X-API-Key": api_key},
                timeout=10,
            )
        except Exception as exc:
            logger.warning("Failed to send security alert: %s", exc)

