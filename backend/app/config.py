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

    meeting_baas_api_key: str | None = None
    meeting_baas_url: str = "https://api.meetingbaas.com/v2/bots"
    meeting_baas_input_url: str | None = None
    meeting_baas_webhook_secret: str | None = None
    embedding_provider: str = "openai"
    embedding_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    embedding_batch_size: int = 64
    embedding_max_chunks: int = 500
    r2_endpoint_url: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket_name: str | None = None
    r2_presigned_expiry_seconds: int = 600
    groq_api_key: str | None = None
    groq_stt_model: str = "whisper-large-v3-turbo"
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
