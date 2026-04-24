import keyring
import json
import os
from typing import Optional
from ..config import config

class CredentialStore:
    def __init__(self):
        # Store credentials in the same directory as the log file
        self.file_path = os.path.join(os.path.dirname(config.LOG_FILE), "credentials.json")

    def _active_file(self) -> dict:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_file(self, data: dict) -> None:
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"DEBUG: Failed to save credentials file: {e}")

    def set(self, key: str, value: str) -> None:
        # Try keyring first
        try:
            keyring.set_password(config.KEYRING_SERVICE, key, value)
            return
        except Exception as e:
            print(f"DEBUG: Keyring set failed ({e}), using fallback file.")

        # Fallback to file
        data = self._active_file()
        data[key] = value
        self._save_file(data)

    def get(self, key: str) -> Optional[str]:
        # Try keyring first
        try:
            val = keyring.get_password(config.KEYRING_SERVICE, key)
            if val is not None:
                return val
        except Exception:
            pass

        # Fallback to file
        data = self._active_file()
        return data.get(key)

    def clear(self, key: str) -> None:
        try:
            keyring.delete_password(config.KEYRING_SERVICE, key)
        except Exception:
            pass

        # Clear from file
        data = self._active_file()
        if key in data:
            del data[key]
            self._save_file(data)
