import keyring
from typing import Optional
from ..config import config

class CredentialStore:
    def set(self, key: str, value: str) -> None:
        keyring.set_password(config.KEYRING_SERVICE, key, value)

    def get(self, key: str) -> Optional[str]:
        return keyring.get_password(config.KEYRING_SERVICE, key)

    def clear(self, key: str) -> None:
        try:
            keyring.delete_password(config.KEYRING_SERVICE, key)
        except Exception:
            pass
