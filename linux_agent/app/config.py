import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PI_SERVER_IP = os.getenv("PI_SERVER_IP", "127.0.0.1")
    PI_SERVER_PORT = int(os.getenv("PI_SERVER_PORT", "8000"))
    MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))

    DEVICE_HOSTNAME = os.getenv("DEVICE_HOSTNAME", "AUTO")
    AGENT_VERSION = os.getenv("AGENT_VERSION", "1.0.0")

    TELEMETRY_INTERVAL_SECONDS = int(os.getenv("TELEMETRY_INTERVAL_SECONDS", "30"))
    HEARTBEAT_INTERVAL_SECONDS = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "60"))

    RECONNECT_INTERVAL_SECONDS = int(os.getenv("RECONNECT_INTERVAL_SECONDS", "5"))
    MAX_RECONNECT_ATTEMPTS = int(os.getenv("MAX_RECONNECT_ATTEMPTS", "0"))

    ACTIVITY_IDLE_THRESHOLD_SECONDS = int(os.getenv("ACTIVITY_IDLE_THRESHOLD_SECONDS", "300"))

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "/var/log/sentinelpi/agent.log")

    KEYRING_SERVICE = "SentinelPi-EDR"

    SUPABASE_URL = os.getenv("EXPO_PUBLIC_SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("EXPO_PUBLIC_SUPABASE_ANON_KEY", "")

config = Config()

# Export module-level variables for agent.py compatibility
MQTT_BROKER = config.PI_SERVER_IP
MQTT_PORT = config.MQTT_BROKER_PORT
SUPABASE_URL = config.SUPABASE_URL
SUPABASE_KEY = config.SUPABASE_KEY
DEVICE_ID = None
