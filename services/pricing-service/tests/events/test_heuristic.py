"""Tests for the heuristic fallback scorer."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from events.models import NormalizedEvent
from events.scoring.heuristic import (
    CATEGORY_BASE,
    HeuristicScorer,
    heuristic_score,
)


def test_heuristic_score_large_music_event_close() -> None:
    score = heuristic_score(category="MUSIC", expected_attendance=22000, distance_km=2.0)
    assert 40 <= score <= 100


def test_heuristic_score_small_culture_event_far() -> None:
    score = heuristic_score(category="CULTURE", expected_attendance=80, distance_km=12.0)
    assert score <= 10


def test_heuristic_score_zero_attendance() -> None:
    score = heuristic_score(category="MUSIC", expected_attendance=0, distance_km=1.0)
    assert score >= 0


def test_heuristic_score_no_category() -> None:
    score = heuristic_score(category=None, expected_attendance=5000, distance_km=5.0)
    assert 0 <= score <= 100


def test_heuristic_score_clamped_to_100() -> None:
    score = heuristic_score(category="MUSIC", expected_attendance=100000, distance_km=0.1)
    assert score <= 100


def test_heuristic_score_all_categories() -> None:
    for cat in CATEGORY_BASE:
        score = heuristic_score(category=cat, expected_attendance=10000, distance_km=5.0)
        assert 0 <= score <= 100


@pytest.mark.asyncio
async def test_heuristic_scorer_returns_fallback_flag() -> None:
    event = NormalizedEvent(
        provider="static",
        external_id="h-001",
        name="Test",
        category="MUSIC",
        venue_name="V",
        city="K",
        latitude=50.06,
        longitude=19.93,
        distance_km=3.0,
        starts_at=datetime(2027, 6, 14, 19, 0, tzinfo=UTC),
        ends_at=datetime(2027, 6, 14, 23, 0, tzinfo=UTC),
        expected_attendance=10000,
        url=None,
        raw_payload={},
    )
    scorer = HeuristicScorer()
    results = await scorer.score([event])
    assert len(results) == 1
    assert results[0].is_fallback is True
    assert 0 <= results[0].impact_score <= 100
    assert results[0].confidence == "MEDIUM"
    assert len(results[0].affected_nights) >= 1


@pytest.mark.asyncio
async def test_heuristic_eve_night_for_high_score() -> None:
    """Events with high score include the eve (day before) in affected_nights."""
    event = NormalizedEvent(
        provider="static",
        external_id="h-eve",
        name="Huge Concert",
        category="MUSIC",
        venue_name="Arena",
        city="Kraków",
        latitude=50.06,
        longitude=19.93,
        distance_km=1.0,
        starts_at=datetime(2027, 6, 14, 19, 0, tzinfo=UTC),
        ends_at=datetime(2027, 6, 14, 23, 0, tzinfo=UTC),
        expected_attendance=50000,
        url=None,
        raw_payload={},
    )
    scorer = HeuristicScorer()
    results = await scorer.score([event])
    score = results[0]
    if score.impact_score >= 70:
        eve = date(2027, 6, 13)
        assert eve in score.affected_nights
