from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    env: str = "development"
    debug: bool = True
    db_url: str = "postgresql://pfios:pfios@127.0.0.1:5432/pfios"
    redis_url: str = "redis://127.0.0.1:6379/0"
    duckdb_analytics_path: str = "./data/analytics.duckdb"
    audit_log_dir: str = "./data/logs/audit"
    reasoning_provider: str = "mock"
    hermes_base_url: str = "http://127.0.0.1:9120/pfios/v1"
    hermes_api_token: str = ""
    hermes_timeout_seconds: float = 30.0
    hermes_max_retries: int = 1
    hermes_retry_backoff_seconds: float = 0.2
    hermes_default_model: str = "google/gemini-3.1-pro-preview"
    hermes_default_provider: str = "gemini"
    hermes_enable_delegation: bool = True
    hermes_enable_memory: bool = True
    hermes_enable_moa: bool = False
    timezone: str = "Asia/Shanghai"
    sentry_dsn: str = ""
    otel_service_name: str = "aegisos-api"
    otel_exporter_otlp_endpoint: str = ""
    # LLM Response Cache
    llm_cache_enabled: bool = False
    llm_cache_ttl_seconds: int = 900
    llm_cache_namespace: str = "llm:cache:v1"

    model_config = SettingsConfigDict(
        env_prefix="PFIOS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
