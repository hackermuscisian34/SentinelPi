import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PI_SERVER_IP = os.getenv("PI_SERVER_IP", "127.0.0.1")
    PI_SERVER_PORT = int(os.getenv("PI_SERVER_PORT", "8000"))
    PI_SERVER_WEBSOCKET_PORT = int(os.getenv("PI_SERVER_WEBSOCKET_PORT", "8000"))

    DEVICE_HOSTNAME = os.getenv("DEVICE_HOSTNAME", "AUTO")
    AGENT_VERSION = os.getenv("AGENT_VERSION", "1.0.0")

    TELEMETRY_INTERVAL_SECONDS = int(os.getenv("TELEMETRY_INTERVAL_SECONDS", "30"))
    HEARTBEAT_INTERVAL_SECONDS = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "60"))

    RECONNECT_INTERVAL_SECONDS = int(os.getenv("RECONNECT_INTERVAL_SECONDS", "5"))
    MAX_RECONNECT_ATTEMPTS = int(os.getenv("MAX_RECONNECT_ATTEMPTS", "0"))

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "C:\\ProgramData\\SentinelPi\\agent.log")

    KEYRING_SERVICE = "SentinelPi-EDR"

config = Config()
