"""Centralized configuration loaded from environment."""
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API keys
    google_api_key: str
    groq_api_key: str
    spacetrack_username: str
    spacetrack_password: str
    copernicus_username: str
    copernicus_password: str

    # LangSmith
    langsmith_api_key: str | None = None
    langsmith_project: str = "amoa"
    langsmith_tracing: bool = True

    # LLM provider
    amoa_llm_provider: str = "claude"

    # Paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    diskcache_dir: str = ".diskcache"


settings = Settings()
