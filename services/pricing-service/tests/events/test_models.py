"""Tests for event models."""

from __future__ import annotations

from datetime import UTC, date, datetime

from events.models import EventScoreResult, NormalizedEvent


def test_content_hash_deterministic() -> None:
    event = NormalizedEvent(
        provider="static",
        external_id="hash-001",
        name="Test Event",
        category="MUSIC",
        venue_name="Venue",
        city="Kraków",
        latitude=50.06,
        longitude=19.93,
        distance_km=3.0,
        starts_at=datetime(2027, 6, 14, 19, 0, tzinfo=UTC),
        ends_at=datetime(2027, 6, 14, 23, 0, tzinfo=UTC),
        expected_attendance=10000,
        url=None,
        raw_payload={},
    )
    hash1 = event.content_hash
    hash2 = event.content_hash
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex


def test_content_hash_changes_with_name() -> None:
    base = {
        "provider": "static",
        "external_id": "hash-002",
        "category": "MUSIC",
        "venue_name": "V",
        "city": "K",
        "latitude": 50.0,
        "longitude": 19.0,
        "distance_km": 1.0,
        "starts_at": datetime(2027, 1, 1, tzinfo=UTC),
        "ends_at": None,
        "expected_attendance": 100,
        "url": None,
        "raw_payload": {},
    }
    e1 = NormalizedEvent(name="Event A", **base)
    e2 = NormalizedEvent(name="Event B", **base)
    assert e1.content_hash != e2.content_hash


def test_score_clamped_to_0_100() -> None:
    result = EventScoreResult(
        event_external_id="clamp-001",
        impact_score=150,
        confidence="HIGH",
        affected_nights=[date(2027, 6, 14)],
        rationale="Test",
    )
    assert result.impact_score == 100

    result_neg = EventScoreResult(
        event_external_id="clamp-002",
        impact_score=-10,
        confidence="LOW",
    )
    assert result_neg.impact_score == 0
