from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    env: str = Field(default="prod")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    supabase_url: str = Field(default="")
    supabase_service_role_key: str = Field(default="")
    supabase_anon_key: str = Field(default="")

    jwt_audience: str = Field(default="authenticated")

    pairing_code_ttl_seconds: int = Field(default=300)
    device_token_ttl_seconds: int = Field(default=31536000)

    telemetry_flush_interval_seconds: int = Field(default=10)
    telemetry_buffer_db_path: str = Field(default="/var/lib/sentinelpi/telemetry.db")

    log_level: str = Field(default="INFO")

    allowed_origins: List[str] = Field(default_factory=lambda: ["*"])

    class Config:
        env_prefix = "SENTINELPI_"
        case_sensitive = False

settings = Settings()
