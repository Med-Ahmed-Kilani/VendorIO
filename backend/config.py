from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql://vendorio:vendorio@localhost:5432/vendorio_db"
    fastapi_env: str = "development"
    log_level: str = "INFO"
    forecast_retrain_days: int = 7
    ordering_cost: float = 25.0
    holding_cost_rate: float = 0.25
    secret_key: str = "change-me-in-production"

    @property
    def is_development(self) -> bool:
        return self.fastapi_env == "development"


settings = Settings()
