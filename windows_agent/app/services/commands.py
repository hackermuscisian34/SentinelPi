import subprocess
from typing import Dict, Any
import os

class CommandExecutor:
    def execute(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if command == "shutdown":
                subprocess.Popen(["shutdown", "/s", "/t", "0"], shell=False)
                return {"status": "ok"}
            if command == "restart":
                subprocess.Popen(["shutdown", "/r", "/t", "0"], shell=False)
                return {"status": "ok"}
            if command == "kill_process":
                pid = str(args.get("pid"))
                subprocess.check_output(["taskkill", "/PID", pid, "/F"], text=True)
                return {"status": "ok"}
            if command == "isolate_network":
                self._set_network_state(False)
                return {"status": "ok"}
            if command == "restore_network":
                self._set_network_state(True)
                return {"status": "ok"}
            if command == "trigger_scan":
                path = args.get("path", "C:\\")
                return self._run_clamav(path)
            return {"status": "error", "message": "Unknown command"}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def _set_network_state(self, enable: bool) -> None:
        state = "enabled" if enable else "disabled"
        subprocess.check_output(
            ["powershell", "-Command", f"Get-NetAdapter | Where-Object {{$_.Status -eq 'Up'}} | ForEach-Object {{Disable-NetAdapter -Name $_.Name -Confirm:$false}}"],
            text=True,
        ) if not enable else subprocess.check_output(
            ["powershell", "-Command", "Get-NetAdapter | Where-Object {$_.Status -eq 'Disabled'} | ForEach-Object {Enable-NetAdapter -Name $_.Name -Confirm:$false}"],
            text=True,
        )

    def _run_clamav(self, path: str) -> Dict[str, Any]:
        try:
            clamscan = os.getenv("CLAMAV_PATH", "clamscan.exe")
            output = subprocess.check_output([clamscan, "-r", path], text=True)
            return {"status": "ok", "output": output}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}
