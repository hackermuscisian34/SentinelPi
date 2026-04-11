import logging
import subprocess
import threading
import winreg
from typing import Callable, Optional

logger = logging.getLogger("agent.camera_monitor")

# Registry path where Windows logs active camera sessions per app
_CAM_KEYS = [
    (winreg.HKEY_LOCAL_MACHINE,
     r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam"),
    (winreg.HKEY_CURRENT_USER,
     r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam"),
]


def _friendly_app_name(raw: str) -> str:
    """Convert a registry key name to a human-readable app label."""
    # NonPackaged entries look like:
    #   NonPackaged\C:#Windows#System32#some.exe
    # UWP entries look like:
    #   Microsoft.WindowsCamera_8wekyb3d8bbwe
    if "#" in raw:
        # desktop / NonPackaged entry — reconstruct the exe path
        parts = raw.replace("#", "\\")
        exe = parts.split("\\")[-1]
        return exe  # e.g. "zoom.exe"
    # UWP package family name — strip the publisher hash at the end
    name = raw.split("_")[0]          # e.g. "Microsoft.WindowsCamera"
    name = name.split(".")[-1]        # e.g. "WindowsCamera"
    # Insert spaces before upper-case letters for readability
    import re
    name = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)
    return name                        # e.g. "Windows Camera"


def _get_active_camera_sessions() -> dict[str, str]:
    """
    Return a dict mapping registry-key → friendly-name for every app that
    currently has an open camera session (LastUsedTimeStop == 0).
    """
    sessions: dict[str, str] = {}

    for hive, path in _CAM_KEYS:
        try:
            root = winreg.OpenKey(hive, path)
        except OSError:
            continue

        with root:
            idx = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(root, idx)
                    idx += 1
                except OSError:
                    break

                try:
                    subkey = winreg.OpenKey(root, subkey_name)
                    with subkey:
                        if subkey_name == "NonPackaged":
                            # Desktop apps stored one level deeper
                            np_idx = 0
                            while True:
                                try:
                                    np_name = winreg.EnumKey(subkey, np_idx)
                                    np_idx += 1
                                except OSError:
                                    break
                                try:
                                    np_key = winreg.OpenKey(subkey, np_name)
                                    with np_key:
                                        stop, _ = winreg.QueryValueEx(np_key, "LastUsedTimeStop")
                                        if stop == 0:
                                            key = f"NonPackaged\\{np_name}"
                                            sessions[key] = _friendly_app_name(np_name)
                                except OSError:
                                    pass
                        else:
                            # UWP / packaged app
                            try:
                                stop, _ = winreg.QueryValueEx(subkey, "LastUsedTimeStop")
                                if stop == 0:
                                    sessions[subkey_name] = _friendly_app_name(subkey_name)
                            except OSError:
                                pass
                except OSError:
                    pass

    return sessions


class CameraMonitor:
    """
    Detects when any application activates the webcam/camera by polling
    the Windows CapabilityAccessManager registry key every 3 seconds.

    Fires alert_callback(title, description, severity) when:
      • a new app starts using the camera  →  🔴 camera LED on
      • an app stops using the camera     →  🟢 camera LED off
    """

    def __init__(self, alert_callback: Callable[[str, str, str], None]):
        self.alert_callback = alert_callback
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._active: dict[str, str] = {}   # key → friendly name

    # ------------------------------------------------------------------
    def start(self) -> None:
        self._stop_event.clear()
        self._active = _get_active_camera_sessions()
        self._thread = threading.Thread(target=self._run, daemon=True, name="CameraMonitor")
        self._thread.start()
        logger.info("CameraMonitor started (polling interval 3s)")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    # ------------------------------------------------------------------
    def _run(self) -> None:
        POLL_INTERVAL = 3  # seconds — fast enough to feel real-time

        while not self._stop_event.is_set():
            try:
                current = _get_active_camera_sessions()

                # ── New camera sessions (LED just turned ON) ──────────
                for key, app_name in current.items():
                    if key not in self._active:
                        logger.warning("📷 Camera opened by: %s", app_name)
                        self.alert_callback(
                            "📷 Camera Activated",
                            f'"{app_name}" just opened the camera — '
                            f"the camera LED is now ON.",
                            "critical",
                        )

                # ── Ended camera sessions (LED just turned OFF) ───────
                for key, app_name in self._active.items():
                    if key not in current:
                        logger.info("📷 Camera closed by: %s", app_name)
                        self.alert_callback(
                            "📷 Camera Deactivated",
                            f'"{app_name}" closed the camera — '
                            f"the camera LED is now OFF.",
                            "info",
                        )

                self._active = current

            except Exception as exc:
                logger.error("CameraMonitor poll error: %s", exc)

            self._stop_event.wait(POLL_INTERVAL)
