from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    openai_api_key: str = Field(default="")
    openai_chat_model: str = Field(default="gpt-4o-mini")
    openai_embedding_model: str = Field(default="text-embedding-3-small")
    data_dir: Path = Field(default=Path("./data"))
    database_url: str = Field(...)
    upload_dir: Path = Field(default=Path("./data/uploads"))
    cors_origins: str = Field(default="http://localhost:3000")
    max_upload_mb: int = Field(default=100)
    max_concurrent_pipelines: int = Field(default=5)
    db_pool_min: int = Field(default=2)
    db_pool_max: int = Field(default=20)
    chat_rate_limit: str = Field(default="20/minute")
    upload_rate_limit: str = Field(default="5/minute")
    api_key: str = Field(default="")
    langfuse_public_key: str = Field(default="", validation_alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", validation_alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com",
        validation_alias="LANGFUSE_HOST"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def ensure_dirs(self) -> None:
        for p in (self.data_dir, self.upload_dir):
            Path(p).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s
