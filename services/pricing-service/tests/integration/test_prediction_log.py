"""DB integration tests with testcontainers Postgres."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.services.model_loader import load_fixture_model
from app.settings import Settings
from ml.features import FEATURE_SCHEMA_HASH
from tests.api.conftest import API_KEY, FIXTURE_DIR

ALEMBIC_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def pg_url() -> Iterator[str]:
    pytest.importorskip("testcontainers")
    try:
        from testcontainers.community.postgres import PostgresContainer
    except ImportError:  # older testcontainers package layout
        from testcontainers.postgres import PostgresContainer

    try:
        postgres = PostgresContainer("postgres:17")
        postgres.start()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Docker/testcontainers unavailable: {exc}")

    try:
        url = postgres.get_connection_url()
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql+psycopg2://"):
            url = url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
        os.environ["PRICING_DATABASE_URL"] = url

        engine = sa.create_engine(url)
        with engine.begin() as conn:
            conn.execute(sa.text("CREATE SCHEMA IF NOT EXISTS pricing"))

        from alembic import command
        from alembic.config import Config

        cfg = Config(str(ALEMBIC_ROOT / "alembic.ini"))
        cfg.set_main_option("script_location", str(ALEMBIC_ROOT / "migrations"))
        command.upgrade(cfg, "head")

        model = load_fixture_model(FIXTURE_DIR)
        assert model is not None
        meta = json.loads((FIXTURE_DIR / "metadata.json").read_text(encoding="utf-8"))
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO pricing.model_registry (
                        version, algorithm, dataset_hash, params, metrics,
                        feature_schema_hash, artifact_path, trained_at, is_active
                    ) VALUES (
                        :version, :algorithm, :dataset_hash, CAST(:params AS jsonb),
                        CAST(:metrics AS jsonb), :feature_schema_hash, :artifact_path,
                        :trained_at, true
                    )
                    """
                ),
                {
                    "version": model.version,
                    "algorithm": "RandomForestRegressor",
                    "dataset_hash": "fixture",
                    "params": json.dumps(meta.get("config", {})),
                    "metrics": json.dumps(meta.get("metrics", {})),
                    "feature_schema_hash": FEATURE_SCHEMA_HASH,
                    "artifact_path": str((FIXTURE_DIR / "model.joblib").resolve()),
                    "trained_at": meta["trained_at"],
                },
            )
            conn.execute(
                sa.text(
                    """
                    INSERT INTO pricing.daily_demand (date, indicator, top_event_ids)
                    VALUES (:d, 75, '{}'::bigint[])
                    """
                ),
                {"d": date(2024, 6, 15)},
            )
        engine.dispose()
        yield url
    finally:
        postgres.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_quotes_write_prediction_log_and_join_demand(pg_url: str) -> None:
    settings = Settings(
        PRICING_DATABASE_URL=pg_url,
        INTERNAL_API_KEY=API_KEY,
        MODEL_ARTIFACT_DIR=FIXTURE_DIR,
        ALLOW_FIXTURE_MODEL=True,
    )
    engine = sa.create_engine(pg_url, pool_pre_ping=True)
    model = load_fixture_model(FIXTURE_DIR)
    app = create_app(settings, engine=engine, initial_model=model)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/quotes",
            headers={"X-Internal-Api-Key": API_KEY},
            json={
                "requestId": str(uuid4()),
                "currency": "PLN",
                "items": [
                    {
                        "roomTypeCode": "STD",
                        "date": "2024-06-15",
                        "basePrice": 250.0,
                        "minPrice": 180.0,
                        "maxPrice": 450.0,
                        "occupancyRate": 0.7,
                        "roomsRemaining": 3,
                        "leadTimeDays": 14,
                    }
                ],
            },
        )
        assert response.status_code == 200
        assert response.json()["items"][0]["demandIndicator"] == 75
        await client.get("/health/live")

    with engine.connect() as conn:
        count = conn.execute(sa.text("SELECT count(*) FROM pricing.prediction_log")).scalar_one()
    assert int(count) >= 1
    engine.dispose()
