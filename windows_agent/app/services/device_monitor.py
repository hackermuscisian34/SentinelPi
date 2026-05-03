import logging
import threading

from typing import Callable

logger = logging.getLogger("agent.device_monitor")


class DeviceMonitor:
    """
    Monitors USB / removable device connect & disconnect events on Windows.
    Uses WMI (Win32_DiskDrive) polled every 3 seconds as a fallback that
    works without admin privileges.  If the `wmi` package is available,
    it additionally subscribes to Win32_DeviceChangeEvent for real-time
    notifications.
    """

    def __init__(self, alert_callback: Callable[[str, str, str], None]):
        """
        alert_callback(title, description, severity)
        """
        self.alert_callback = alert_callback
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._known_drives: set[str] = set()

    # ------------------------------------------------------------------
    def start(self) -> None:
        self._stop_event.clear()
        self._known_drives = self._get_removable_drives()
        self._thread = threading.Thread(target=self._run, daemon=True, name="DeviceMonitor")
        self._thread.start()
        logger.info("DeviceMonitor started (polling removable drives)")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    # ------------------------------------------------------------------
    def _get_removable_drives(self) -> set[str]:
        """Return a set of device IDs for currently connected removable drives."""
        drives: set[str] = set()
        try:
            import subprocess, json
            ps_cmd = (
                "Get-WmiObject Win32_DiskDrive | "
                "Where-Object {$_.MediaType -like '*Removable*' -or $_.InterfaceType -eq 'USB'} | "
                "Select-Object DeviceID, Caption, InterfaceType | "
                "ConvertTo-Json"
            )
            out = subprocess.check_output(
                ["powershell", "-Command", ps_cmd],
                text=True, timeout=10
            ).strip()
            if out:
                data = json.loads(out)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    drives.add(item.get("DeviceID", ""))
        except Exception as exc:
            logger.debug("Drive poll error: %s", exc)
        return drives

    def _get_drive_info(self) -> list[dict]:
        """Return rich info about currently connected removable drives."""
        drives = []
        try:
            import subprocess, json
            ps_cmd = (
                "Get-WmiObject Win32_DiskDrive | "
                "Where-Object {$_.MediaType -like '*Removable*' -or $_.InterfaceType -eq 'USB'} | "
                "Select-Object DeviceID, Caption, InterfaceType, Size | "
                "ConvertTo-Json"
            )
            out = subprocess.check_output(
                ["powershell", "-Command", ps_cmd],
                text=True, timeout=10
            ).strip()
            if out:
                data = json.loads(out)
                if isinstance(data, dict):
                    data = [data]
                drives = data
        except Exception as exc:
            logger.debug("Drive info error: %s", exc)
        return drives

    # ------------------------------------------------------------------
    def _run(self) -> None:
        POLL_INTERVAL = 3  # seconds

        while not self._stop_event.is_set():
            try:
                current = self._get_removable_drives()

                # Newly connected
                for device_id in current - self._known_drives:
                    # Get details for this specific device
                    details = [d for d in self._get_drive_info() if d.get("DeviceID") == device_id]
                    caption = details[0].get("Caption", "Unknown device") if details else "Unknown device"
                    iface = details[0].get("InterfaceType", "USB") if details else "USB"
                    logger.warning("Foreign device connected: %s (%s)", caption, device_id)
                    self.alert_callback(
                        "⚠️ Foreign Device Connected",
                        f"{iface} device connected: {caption} [{device_id}]",
                        "high"
                    )

                # Disconnected
                for device_id in self._known_drives - current:
                    logger.info("Device disconnected: %s", device_id)
                    self.alert_callback(
                        "🔌 Device Disconnected",
                        f"External device removed: {device_id}",
                        "medium"
                    )

                self._known_drives = current

            except Exception as exc:
                logger.error("DeviceMonitor poll error: %s", exc)

            self._stop_event.wait(POLL_INTERVAL)
