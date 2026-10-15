"""Tests for EventProvider adapters: Static + Ticketmaster."""

from __future__ import annotations

from pathlib import Path

import pytest

from events.providers.static import StaticFileEventProvider

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "events" / "static_events.json"


@pytest.mark.asyncio
async def test_static_provider_loads_all_events() -> None:
    provider = StaticFileEventProvider(FIXTURE_PATH)
    events = await provider.fetch_events()
    assert len(events) == 20
    assert all(e.provider == "static" for e in events)
    assert all(e.starts_at is not None for e in events)


@pytest.mark.asyncio
async def test_static_provider_missing_file() -> None:
    provider = StaticFileEventProvider(Path("/nonexistent/events.json"))
    events = await provider.fetch_events()
    assert events == []


@pytest.mark.asyncio
async def test_static_events_have_required_fields() -> None:
    provider = StaticFileEventProvider(FIXTURE_PATH)
    events = await provider.fetch_events()
    for event in events:
        assert event.external_id, f"Missing external_id: {event.name}"
        assert event.name
        assert event.starts_at is not None
        assert event.content_hash  # SHA-256 hex


@pytest.mark.asyncio
async def test_static_events_injection_canary_present() -> None:
    """The fixture includes an event with an injection attempt in its name."""
    provider = StaticFileEventProvider(FIXTURE_PATH)
    events = await provider.fetch_events()
    injection_events = [e for e in events if "IGNORE ALL INSTRUCTIONS" in e.name]
    assert len(injection_events) == 1
    assert injection_events[0].external_id == "static-018"


@pytest.mark.asyncio
async def test_ticketmaster_provider_pagination() -> None:
    """Ticketmaster pagination with respx mock."""
    respx = pytest.importorskip("respx")
    import httpx

    from events.providers.ticketmaster import TicketmasterProvider

    page0_data = {
        "_embedded": {
            "events": [
                {
                    "id": "tm-001",
                    "name": "Test Concert",
                    "dates": {
                        "start": {"dateTime": "2027-06-14T19:00:00Z"},
                        "end": {"dateTime": "2027-06-14T23:00:00Z"},
                    },
                    "_embedded": {
                        "venues": [
                            {
                                "name": "Test Venue",
                                "city": {"name": "Kraków"},
                                "location": {
                                    "latitude": "50.065",
                                    "longitude": "20.010",
                                },
                            }
                        ]
                    },
                    "classifications": [{"segment": {"name": "Music"}}],
                }
            ]
        },
        "page": {"totalPages": 1, "number": 0},
    }

    async with respx.mock:
        respx.get("https://app.ticketmaster.com/discovery/v2/events.json").mock(
            return_value=httpx.Response(200, json=page0_data)
        )

        async with httpx.AsyncClient() as client:
            provider = TicketmasterProvider(
                api_key="test-key",
                hotel_lat=50.068369,
                hotel_lon=19.924854,
                client=client,
            )
            events = await provider.fetch_events()

    assert len(events) == 1
    assert events[0].provider == "ticketmaster"
    assert events[0].external_id == "tm-001"
    assert events[0].category == "MUSIC"
    assert events[0].distance_km is not None


@pytest.mark.asyncio
async def test_ticketmaster_429_backoff() -> None:
    """Ticketmaster rate-limit handling: 429 then success."""
    respx = pytest.importorskip("respx")
    import httpx

    from events.providers.ticketmaster import TicketmasterProvider

    call_count = 0
    page_data = {
        "_embedded": {
            "events": [
                {
                    "id": "tm-retry",
                    "name": "Retry Event",
                    "dates": {"start": {"dateTime": "2027-07-01T20:00:00Z"}},
                    "_embedded": {
                        "venues": [
                            {
                                "name": "V",
                                "city": {"name": "K"},
                                "location": {"latitude": "50.06", "longitude": "19.93"},
                            }
                        ]
                    },
                    "classifications": [{"segment": {"name": "Sports"}}],
                }
            ]
        },
        "page": {"totalPages": 1},
    }

    def side_effect(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(429)
        return httpx.Response(200, json=page_data)

    async with respx.mock:
        respx.get("https://app.ticketmaster.com/discovery/v2/events.json").mock(
            side_effect=side_effect
        )
        async with httpx.AsyncClient() as client:
            provider = TicketmasterProvider(
                api_key="test-key",
                hotel_lat=50.068369,
                hotel_lon=19.924854,
                client=client,
            )
            events = await provider.fetch_events()

    assert len(events) == 1
    assert call_count >= 2


@pytest.mark.asyncio
async def test_ticketmaster_malformed_event_skipped() -> None:
    """Events missing id or name are silently skipped."""
    respx = pytest.importorskip("respx")
    import httpx

    from events.providers.ticketmaster import TicketmasterProvider

    page_data = {
        "_embedded": {
            "events": [
                {
                    "id": "",
                    "name": "No ID Event",
                    "dates": {"start": {"dateTime": "2027-07-01T20:00:00Z"}},
                },
                {
                    "id": "tm-ok",
                    "name": "",
                    "dates": {"start": {"dateTime": "2027-07-01T20:00:00Z"}},
                },
                {
                    "id": "tm-good",
                    "name": "Good Event",
                    "dates": {"start": {"dateTime": "2027-07-01T20:00:00Z"}},
                    "_embedded": {
                        "venues": [
                            {
                                "name": "V",
                                "city": {"name": "K"},
                                "location": {"latitude": "50.06", "longitude": "19.93"},
                            }
                        ]
                    },
                },
            ]
        },
        "page": {"totalPages": 1},
    }

    async with respx.mock:
        respx.get("https://app.ticketmaster.com/discovery/v2/events.json").mock(
            return_value=httpx.Response(200, json=page_data)
        )
        async with httpx.AsyncClient() as client:
            provider = TicketmasterProvider(
                api_key="test-key", hotel_lat=50.068369, hotel_lon=19.924854, client=client
            )
            events = await provider.fetch_events()

    assert len(events) == 1
    assert events[0].external_id == "tm-good"
