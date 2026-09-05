from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"
    database_url: str | None = None
    db_pool_size: int = 5
    db_max_overflow: int = 10
    upstash_redis_url: str | None = None
    realtime_require_broker: bool = False

    meeting_baas_api_key: str | None = None
    meeting_baas_url: str = "https://api.meetingbaas.com/v2/bots"
    meeting_baas_input_url: str | None = None
    meeting_baas_webhook_secret: str | None = None
    meeting_baas_timeout_seconds: float = 10.0
    meeting_baas_max_retries: int = 2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    neon_auth_issuer: str | None = None
    neon_auth_base_url: str | None = None
    neon_auth_audience: str | None = None
    neon_auth_jwks_url: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def database_configured(self) -> bool:
        return bool(self.database_url)

    @property
    def realtime_broker_configured(self) -> bool:
        return bool(self.upstash_redis_url)

    @property
    def neon_auth_configured(self) -> bool:
        return bool(
            self.neon_auth_issuer and self.neon_auth_audience and self.neon_auth_jwks_url
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
