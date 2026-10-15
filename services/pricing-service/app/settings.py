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

    # --- Event intelligence (Phase 7) ---
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    prompt_version: str = Field(default="event-impact-v1", alias="PROMPT_VERSION")
    gemini_daily_call_budget: int = Field(default=200, alias="GEMINI_DAILY_CALL_BUDGET")
    ticketmaster_api_key: str = Field(default="", alias="TICKETMASTER_API_KEY")
    event_provider: str = Field(default="static", alias="EVENT_PROVIDER")
    hotel_lat: float = Field(default=50.068369, alias="HOTEL_LAT")
    hotel_lon: float = Field(default=19.924854, alias="HOTEL_LON")
    event_radius_km: float = Field(default=15.0, alias="EVENT_RADIUS_KM")
    event_horizon_days: int = Field(default=120, alias="EVENT_HORIZON_DAYS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
