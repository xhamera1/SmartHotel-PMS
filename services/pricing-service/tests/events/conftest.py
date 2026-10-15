"""Shared fixtures for events tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from events.models import NormalizedEvent

WARSAW_TZ_OFFSET = UTC  # tests use UTC for simplicity


@pytest.fixture
def sample_events() -> list[NormalizedEvent]:
    return [
        NormalizedEvent(
            provider="static",
            external_id="test-001",
            name="Metallica Concert",
            category="MUSIC",
            venue_name="TAURON Arena",
            city="Kraków",
            latitude=50.0653,
            longitude=20.0106,
            distance_km=6.5,
            starts_at=datetime(2027, 6, 14, 19, 0, tzinfo=UTC),
            ends_at=datetime(2027, 6, 14, 23, 0, tzinfo=UTC),
            expected_attendance=22000,
            url="https://example.com",
            raw_payload={"id": "test-001", "name": "Metallica Concert"},
        ),
        NormalizedEvent(
            provider="static",
            external_id="test-002",
            name="Small Gallery Opening",
            category="CULTURE",
            venue_name="Galeria",
            city="Kraków",
            latitude=50.058,
            longitude=19.937,
            distance_km=1.3,
            starts_at=datetime(2027, 8, 15, 18, 0, tzinfo=UTC),
            ends_at=datetime(2027, 8, 15, 21, 0, tzinfo=UTC),
            expected_attendance=80,
            url=None,
            raw_payload={"id": "test-002", "name": "Small Gallery Opening"},
        ),
        NormalizedEvent(
            provider="static",
            external_id="test-003",
            name="Tech Conference 2027",
            category="CONFERENCE",
            venue_name="ICE Kraków",
            city="Kraków",
            latitude=50.047,
            longitude=19.934,
            distance_km=2.4,
            starts_at=datetime(2027, 5, 12, 9, 0, tzinfo=UTC),
            ends_at=datetime(2027, 5, 14, 18, 0, tzinfo=UTC),
            expected_attendance=5000,
            url="https://example.com/conf",
            raw_payload={"id": "test-003", "name": "Tech Conference 2027"},
        ),
    ]
