from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables / .env files."""

    model_config = SettingsConfigDict(
        env_prefix="LOCALLIFT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    environment: str = Field(default="local", description="Deployment environment name")
    log_level: str = Field(default="INFO", description="Log level for the pipeline")

    # Data ingestion
    tcad_base_url: str = Field(
        default="https://gis.traviscountytx.gov/server1/rest/services/Boundaries_and_Jurisdictions/TCAD/MapServer/0",
        description="Base REST endpoint for the TCAD property layer (full dataset with all properties)",
    )
    tcad_page_size: int = Field(default=1000, ge=1, le=2000, description="Records per page (reduced from 2000 to avoid transfer limit with geometry)")
    tcad_concurrency: int = Field(
        default=4,
        description="Maximum number of concurrent page fetches",
        ge=1,
        le=16,
    )
    request_timeout_seconds: float = Field(default=30.0, gt=0)
    request_retry_attempts: int = Field(default=5, ge=0, le=10)
    request_retry_backoff: float = Field(default=0.5, gt=0)

    # Persistence
    database_url: str = Field(
        default="postgresql+asyncpg://locallift:locallift_dev@localhost:5433/locallift",
        description="Async SQLAlchemy connection URL",
    )
    database_echo: bool = Field(default=False)

    # File output (optional export of raw JSON for diagnostics)
    export_dir: Path | None = Field(
        default=None,
        description="Optional path to write raw API responses for auditing",
    )
    
    # Contact enrichment (Hunter.io)
    hunter_io_api_key: str | None = Field(
        default=None,
        description="Hunter.io API key for contact enrichment (required for Phase 1)",
    )
    hunter_io_rate_limit_per_minute: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Hunter.io API rate limit (requests per minute) - adjust based on plan",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


__all__ = ["Settings", "get_settings"]
