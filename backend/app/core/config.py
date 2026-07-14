from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Prompt Generator API"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_v1_prefix: str = "/api/v1"
    database_url: str
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    auto_create_tables: bool = True
    ai_provider: str = "openai"
    openai_api_key: str | None = Field(default=None, repr=False)
    openai_model: str = "gpt-5.4-mini"
    openai_timeout_seconds: float = 45.0
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:4b-instruct"
    ollama_timeout_seconds: float = 420.0

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def openai_enabled(self) -> bool:
        return self.ai_provider.lower() == "openai" and bool(self.openai_api_key)

    @property
    def ollama_enabled(self) -> bool:
        return self.ai_provider.lower() == "ollama"

    @property
    def ai_configured(self) -> bool:
        return self.openai_enabled or self.ollama_enabled


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
