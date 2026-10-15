"""pydantic-settings for the pricing microservice (Appendix A)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_ROOT = Path(__file__).resolve().parent
SERVICE_ROOT = PACKAGE_ROOT.parent
REPO_ROOT = SERVICE_ROOT.parents[1]
DEFAULT_FIXTURE_MODEL = SERVICE_ROOT / "fixtures" / "models" / "tiny"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    pricing_database_url: str = Field(
        default="postgresql+psycopg://pricing_user:pricing-dev-password@localhost:5432/smarthotel",
        alias="PRICING_DATABASE_URL",
    )
    internal_api_key: str = Field(default="dev-internal-api-key", alias="INTERNAL_API_KEY")
    model_artifact_dir: Path = Field(
        default=DEFAULT_FIXTURE_MODEL,
        alias="MODEL_ARTIFACT_DIR",
    )
    allow_fixture_model: bool = Field(default=True, alias="ALLOW_FIXTURE_MODEL")
    host: str = Field(default="0.0.0.0", alias="PRICING_HOST")
    port: int = Field(default=8081, alias="PRICING_PORT")


@lru_cache
def get_settings() -> Settings:
    return Settings()
