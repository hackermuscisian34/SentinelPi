from typing import Dict, Any
from datetime import datetime, timedelta
import secrets
import string
from ..config import settings

class PairingManager:
    def __init__(self) -> None:
        self._codes: Dict[str, Dict[str, Any]] = {}

    def _generate_code(self, length: int = 6) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def create(self, device_name: str) -> Dict[str, Any]:
        code = self._generate_code()
        expires_at = datetime.utcnow() + timedelta(seconds=settings.pairing_code_ttl_seconds)
        self._codes[code] = {
            "device_name": device_name,
            "expires_at": expires_at,
        }
        return {"pairing_code": code, "expires_at": expires_at.isoformat()}

    def verify(self, code: str) -> Dict[str, Any] | None:
        entry = self._codes.get(code)
        if not entry:
            return None
        if entry["expires_at"] < datetime.utcnow():
            self._codes.pop(code, None)
            return None
        return entry

    def consume(self, code: str) -> None:
        self._codes.pop(code, None)
