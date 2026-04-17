from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "development"
    debug: bool = True
    db_url: str = "duckdb:///./data/pfios.duckdb"
    audit_log_dir: str = "./data/logs/audit"
    reasoning_provider: str = "mock"
    timezone: str = "Asia/Shanghai"

    model_config = SettingsConfigDict(
        env_prefix="PFIOS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
