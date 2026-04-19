from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações dos serviços, carregadas de ambiente/.env.
    Todas as configs passam por aqui evita `os.getenv` espalhado pelo código.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://finance:finance@localhost:5432/finance"
    app_env: str = "dev"
    api_key: str = "dev-local-key"
    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, v: object) -> object:
        """Aceita CSV no .env (`a,b,c`) além de JSON list — `.env` não tem tipo lista nativo."""
        if isinstance(v, str) and not v.startswith("["):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    """
    reparsing do .env a cada chamada.
    """
    return Settings()