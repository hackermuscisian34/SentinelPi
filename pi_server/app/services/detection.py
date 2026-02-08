import asyncio
from typing import List, Dict, Any
from datetime import datetime

SUSPICIOUS_PROCESS_KEYWORDS = [
    "mimikatz",
    "rundll32",
    "powershell -enc",
    "certutil",
    "bitsadmin",
]

class DetectionEngine:
    async def analyze_telemetry(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        alerts: List[Dict[str, Any]] = []
        processes = payload.get("processes", [])
        for proc in processes:
            name = (proc.get("name") or "").lower()
            cmd = (proc.get("cmdline") or "").lower()
            for keyword in SUSPICIOUS_PROCESS_KEYWORDS:
                if keyword in name or keyword in cmd:
                    alerts.append(
                        {
                            "timestamp": datetime.utcnow().isoformat(),
                            "severity": "high",
                            "title": "Suspicious process",
                            "description": f"Process matched rule: {keyword}",
                            "metadata": {"process": proc},
                        }
                    )
        return alerts

    async def run_clamav_scan(self, path: str) -> Dict[str, Any]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "clamscan",
                "-r",
                path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            return {
                "status": "ok" if proc.returncode in (0, 1) else "error",
                "returncode": proc.returncode,
                "stdout": stdout.decode(errors="ignore"),
                "stderr": stderr.decode(errors="ignore"),
            }
        except FileNotFoundError:
            return {"status": "error", "message": "clamscan not installed"}
