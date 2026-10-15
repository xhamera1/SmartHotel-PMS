"""HTTP API tests for the pricing FastAPI service."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import pytest

from tests.api.conftest import API_KEY


@pytest.mark.asyncio
async def test_live_no_auth(client) -> None:
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"


@pytest.mark.asyncio
async def test_ready_when_model_loaded(client) -> None:
    response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"


@pytest.mark.asyncio
async def test_quotes_requires_api_key(client) -> None:
    response = await client.post(
        "/api/v1/quotes",
        json={"requestId": str(uuid4()), "currency": "PLN", "items": []},
    )
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")


@pytest.mark.asyncio
async def test_quotes_happy_path(client, auth_headers) -> None:
    with patch("app.services.quoting.fetch_demand_by_dates", return_value={}):
        response = await client.post(
            "/api/v1/quotes",
            headers=auth_headers,
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
                        "occupancyRate": 0.6,
                        "roomsRemaining": 4,
                        "leadTimeDays": 14,
                    }
                ],
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert "modelVersion" in body
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["roomTypeCode"] == "STD"
    assert item["date"] == "2024-06-15"
    assert 180 <= float(item["price"]) <= 450
    assert "factors" in item
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_quotes_rejects_unknown_field(client, auth_headers) -> None:
    response = await client.post(
        "/api/v1/quotes",
        headers=auth_headers,
        json={
            "requestId": str(uuid4()),
            "currency": "PLN",
            "extra": True,
            "items": [
                {
                    "roomTypeCode": "STD",
                    "date": "2024-06-15",
                    "basePrice": 250.0,
                    "minPrice": 180.0,
                    "maxPrice": 450.0,
                    "occupancyRate": 0.5,
                    "roomsRemaining": 5,
                    "leadTimeDays": 7,
                }
            ],
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_quotes_rejects_over_400_items(client, auth_headers) -> None:
    item = {
        "roomTypeCode": "STD",
        "date": "2024-06-15",
        "basePrice": 250.0,
        "minPrice": 180.0,
        "maxPrice": 450.0,
        "occupancyRate": 0.5,
        "roomsRemaining": 5,
        "leadTimeDays": 7,
    }
    response = await client.post(
        "/api/v1/quotes",
        headers=auth_headers,
        json={"requestId": str(uuid4()), "currency": "PLN", "items": [item] * 401},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_quotes_rejects_bad_date(client, auth_headers) -> None:
    response = await client.post(
        "/api/v1/quotes",
        headers=auth_headers,
        json={
            "requestId": str(uuid4()),
            "currency": "PLN",
            "items": [
                {
                    "roomTypeCode": "STD",
                    "date": "15-06-2024",
                    "basePrice": 250.0,
                    "minPrice": 180.0,
                    "maxPrice": 450.0,
                    "occupancyRate": 0.5,
                    "roomsRemaining": 5,
                    "leadTimeDays": 7,
                }
            ],
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_model_not_loaded_returns_503(fixture_model, mock_engine) -> None:
    from httpx import ASGITransport, AsyncClient

    from app.main import create_app
    from app.settings import Settings
    from tests.api.conftest import FIXTURE_DIR

    settings = Settings(
        PRICING_DATABASE_URL="postgresql+psycopg://u:p@localhost:5432/db",
        INTERNAL_API_KEY=API_KEY,
        MODEL_ARTIFACT_DIR=FIXTURE_DIR,
        ALLOW_FIXTURE_MODEL=True,
    )
    application = create_app(settings, engine=mock_engine, initial_model=None)
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ready = await client.get("/health/ready")
        assert ready.status_code == 503
        quotes = await client.post(
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
                        "occupancyRate": 0.5,
                        "roomsRemaining": 5,
                        "leadTimeDays": 7,
                    }
                ],
            },
        )
        assert quotes.status_code == 503


@pytest.mark.asyncio
async def test_events_sync_stub(client, auth_headers) -> None:
    response = await client.post("/internal/events/sync", headers=auth_headers)
    assert response.status_code == 202
    assert "Phase 7" in response.json()["detail"]


@pytest.mark.asyncio
async def test_model_endpoint(client, auth_headers) -> None:
    response = await client.get("/api/v1/model", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["isReady"] is True
    assert body["version"]
