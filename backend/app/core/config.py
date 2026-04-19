from functools import lru_cache

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

    database_url: str = "postgresql://finance:finance@localhost:5432/finance"
    app_env: str = "dev"


@lru_cache
def get_settings() -> Settings:
    """
    reparsing do .env a cada chamada.
    """
    return Settings()