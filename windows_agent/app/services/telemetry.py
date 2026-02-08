import psutil
import socket
import subprocess
from datetime import datetime
from typing import List, Dict, Any

class TelemetryCollector:
    def collect(self) -> Dict[str, Any]:
        cpu = {
            "percent": psutil.cpu_percent(interval=0.1),
            "count": psutil.cpu_count(logical=True),
        }
        mem = psutil.virtual_memory()
        memory = {
            "total": mem.total,
            "available": mem.available,
            "percent": mem.percent,
        }

        processes: List[Dict[str, Any]] = []
        for proc in psutil.process_iter(attrs=["pid", "name", "username", "cmdline", "create_time"]):
            try:
                info = proc.info
                processes.append(
                    {
                        "pid": info.get("pid"),
                        "name": info.get("name"),
                        "username": info.get("username"),
                        "cmdline": " ".join(info.get("cmdline") or []),
                        "create_time": info.get("create_time"),
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        net_io = psutil.net_io_counters()
        network = [
            {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
            }
        ]

        logins = []
        for u in psutil.users():
            logins.append({"name": u.name, "host": u.host, "started": u.started})

        usb = self._usb_devices()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": cpu,
            "memory": memory,
            "processes": processes,
            "network": network,
            "logins": logins,
            "usb": usb,
        }

    def _usb_devices(self) -> List[Dict[str, Any]]:
        try:
            output = subprocess.check_output(["powershell", "-Command", "Get-PnpDevice -Class USB | Select-Object -First 20 | ConvertTo-Json"], text=True)
            if not output:
                return []
            data = __import__("json").loads(output)
            if isinstance(data, list):
                return [{"name": d.get("FriendlyName"), "status": d.get("Status")} for d in data]
            return [{"name": data.get("FriendlyName"), "status": data.get("Status")}]
        except Exception:
            return []
