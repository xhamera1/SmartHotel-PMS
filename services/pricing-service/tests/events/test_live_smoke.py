"""Live smoke tests requiring real API keys — excluded from CI.

Run manually: uv run pytest -m external -v
"""

from __future__ import annotations

import os
from datetime import UTC

import pytest

pytestmark = pytest.mark.external


@pytest.mark.asyncio
async def test_ticketmaster_live_fetch() -> None:
    """Fetch real events from Ticketmaster Discovery API."""
    api_key = os.environ.get("TICKETMASTER_API_KEY")
    if not api_key:
        pytest.skip("TICKETMASTER_API_KEY not set")

    from events.providers.ticketmaster import TicketmasterProvider

    provider = TicketmasterProvider(
        api_key=api_key,
        hotel_lat=50.068369,
        hotel_lon=19.924854,
        radius_km=15.0,
        horizon_days=30,
    )
    events = await provider.fetch_events()
    assert isinstance(events, list)
    if events:
        event = events[0]
        assert event.provider == "ticketmaster"
        assert event.external_id
        assert event.starts_at is not None
        print(f"Fetched {len(events)} events from Ticketmaster")


@pytest.mark.asyncio
async def test_gemini_live_score() -> None:
    """Score a single event with real Gemini API."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")

    from datetime import datetime

    from events.models import NormalizedEvent
    from events.scoring.gemini import GeminiScorer

    event = NormalizedEvent(
        provider="test",
        external_id="live-001",
        name="Metallica Concert at TAURON Arena",
        category="MUSIC",
        venue_name="TAURON Arena Kraków",
        city="Kraków",
        latitude=50.0653,
        longitude=20.0106,
        distance_km=6.5,
        starts_at=datetime(2027, 6, 14, 19, 0, tzinfo=UTC),
        ends_at=datetime(2027, 6, 14, 23, 0, tzinfo=UTC),
        expected_attendance=22000,
        url="https://example.com",
        raw_payload={"test": True},
    )

    model = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
    scorer = GeminiScorer(api_key=api_key, model=model)
    results = await scorer.score([event])

    assert len(results) == 1
    result = results[0]
    assert 0 <= result.impact_score <= 100
    assert result.confidence in ("LOW", "MEDIUM", "HIGH")
    assert len(result.affected_nights) >= 1
    assert not result.is_fallback
    print(f"Gemini score: {result.impact_score}, confidence: {result.confidence}")
    print(f"Rationale: {result.rationale}")
