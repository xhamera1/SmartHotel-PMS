"""Dedicated API tests for GET /api/v1/demand-indicators and GET /api/v1/events."""

from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from tests.api.conftest import API_KEY


@pytest.mark.asyncio
async def test_demand_indicators_requires_auth(client) -> None:
    response = await client.get(
        "/api/v1/demand-indicators", params={"from": "2027-01-01", "to": "2027-01-31"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_demand_indicators_invalid_range(client, auth_headers) -> None:
    response = await client.get(
        "/api/v1/demand-indicators",
        headers=auth_headers,
        params={"from": "2027-01-31", "to": "2027-01-01"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_demand_indicators_empty(client, auth_headers) -> None:
    with patch("app.routers.demand.fetch_demand_range", return_value=[]):
        response = await client.get(
            "/api/v1/demand-indicators",
            headers=auth_headers,
            params={"from": "2027-06-01", "to": "2027-06-30"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []


@pytest.mark.asyncio
async def test_demand_indicators_returns_items(client, auth_headers) -> None:
    mock_rows = [
        {"date": date(2027, 6, 14), "indicator": 78, "top_event_ids": [1, 2]},
        {"date": date(2027, 6, 15), "indicator": 45, "top_event_ids": [1]},
    ]
    with patch("app.routers.demand.fetch_demand_range", return_value=mock_rows):
        response = await client.get(
            "/api/v1/demand-indicators",
            headers=auth_headers,
            params={"from": "2027-06-14", "to": "2027-06-15"},
        )
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 2
    assert items[0]["date"] == "2027-06-14"
    assert items[0]["indicator"] == 78
    assert items[0]["topEventIds"] == [1, 2]


# --- Events endpoint ---


@pytest.mark.asyncio
async def test_events_requires_auth(client) -> None:
    response = await client.get(
        "/api/v1/events", params={"from": "2027-01-01", "to": "2027-12-31"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_events_invalid_range(client, auth_headers) -> None:
    response = await client.get(
        "/api/v1/events",
        headers=auth_headers,
        params={"from": "2027-12-31", "to": "2027-01-01"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_events_empty(client, auth_headers) -> None:
    with patch("app.routers.events.fetch_events_range", return_value=[]):
        response = await client.get(
            "/api/v1/events",
            headers=auth_headers,
            params={"from": "2027-06-01", "to": "2027-06-30"},
        )
    assert response.status_code == 200
    assert response.json()["items"] == []


@pytest.mark.asyncio
async def test_events_returns_items(client, auth_headers) -> None:
    mock_rows = [
        {
            "id": 1,
            "name": "Summer Festival",
            "category": "MUSIC",
            "starts_at": datetime(2027, 7, 10, 18, 0, tzinfo=timezone.utc),
            "ends_at": datetime(2027, 7, 10, 23, 0, tzinfo=timezone.utc),
            "impact_score": 72,
            "distance_km": 3.5,
        },
    ]
    with patch("app.routers.events.fetch_events_range", return_value=mock_rows):
        response = await client.get(
            "/api/v1/events",
            headers=auth_headers,
            params={"from": "2027-07-01", "to": "2027-07-31"},
        )
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Summer Festival"
    assert items[0]["impactScore"] == 72
    assert items[0]["distanceKm"] == 3.5
