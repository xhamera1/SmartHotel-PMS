"""Shared fixtures for pricing API tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.services.model_loader import ModelState, load_fixture_model
from app.settings import Settings
from ml.features import FEATURE_SCHEMA_HASH

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "models" / "tiny"
API_KEY = "test-internal-api-key"


@pytest.fixture
def fixture_model() -> ModelState:
    state = load_fixture_model(FIXTURE_DIR)
    assert state is not None
    assert state.feature_schema_hash == FEATURE_SCHEMA_HASH
    return state


@pytest.fixture
def mock_engine() -> MagicMock:
    engine = MagicMock()
    # check_db / SELECT 1
    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    conn.execute = MagicMock(return_value=MagicMock())
    engine.connect.return_value = conn
    begin = MagicMock()
    begin.__enter__ = MagicMock(return_value=conn)
    begin.__exit__ = MagicMock(return_value=False)
    engine.begin.return_value = begin
    return engine


@pytest.fixture
def app(fixture_model: ModelState, mock_engine: MagicMock):
    settings = Settings(
        PRICING_DATABASE_URL="postgresql+psycopg://u:p@localhost:5432/db",
        INTERNAL_API_KEY=API_KEY,
        MODEL_ARTIFACT_DIR=FIXTURE_DIR,
        ALLOW_FIXTURE_MODEL=True,
    )
    application = create_app(
        settings,
        engine=mock_engine,
        initial_model=fixture_model,
    )
    return application


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"X-Internal-Api-Key": API_KEY}
