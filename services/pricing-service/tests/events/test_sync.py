"""Tests for the sync pipeline with mocked provider + scorer."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.settings import Settings
from events.models import EventScoreResult, NormalizedEvent
from events.sync import SyncPipeline


def _make_settings(**overrides) -> Settings:
    defaults = {
        "PRICING_DATABASE_URL": "postgresql+psycopg://u:p@localhost/db",
        "INTERNAL_API_KEY": "test",
        "EVENT_PROVIDER": "static",
        "GEMINI_API_KEY": "",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _sample_event() -> NormalizedEvent:
    return NormalizedEvent(
        provider="static",
        external_id="sync-001",
        name="Sync Test Event",
        category="MUSIC",
        venue_name="Test",
        city="Kraków",
        latitude=50.06,
        longitude=19.93,
        distance_km=3.0,
        starts_at=datetime(2027, 6, 14, 19, 0, tzinfo=UTC),
        ends_at=datetime(2027, 6, 14, 23, 0, tzinfo=UTC),
        expected_attendance=5000,
        url=None,
        raw_payload={"id": "sync-001"},
    )


@pytest.mark.asyncio
async def test_sync_pipeline_with_mocked_deps() -> None:
    """Full pipeline with mocked provider, ingestion, scorer, and aggregation."""
    event = _sample_event()
    settings = _make_settings()

    mock_engine = MagicMock()

    mock_provider = AsyncMock()
    mock_provider.fetch_events.return_value = [event]

    score_result = EventScoreResult(
        event_external_id="sync-001",
        impact_score=65,
        confidence="MEDIUM",
        affected_nights=[datetime(2027, 6, 14).date()],
        rationale="Test rationale",
        is_fallback=True,
    )

    with (
        patch("events.sync._build_provider", return_value=mock_provider),
        patch(
            "events.sync.upsert_events",
            return_value=[{"id": 1, "external_id": "sync-001", "is_new_or_changed": True}],
        ),
        patch("events.sync.mark_stale", return_value=0),
        patch("events.sync.insert_scores"),
        patch("events.sync.get_event_db_id", return_value=1),
        patch("events.sync.HeuristicScorer") as MockHeuristic,
        patch.object(
            SyncPipeline,
            "_load_scored_events_for_aggregation",
            return_value=[
                {
                    "event_db_id": 1,
                    "impact_score": 65,
                    "distance_km": 3.0,
                    "affected_nights": [datetime(2027, 6, 14).date()],
                }
            ],
        ),
        patch("events.sync.upsert_daily_demand", return_value=1),
    ):
        mock_scorer_instance = AsyncMock()
        mock_scorer_instance.score.return_value = [score_result]
        MockHeuristic.return_value = mock_scorer_instance

        pipeline = SyncPipeline(mock_engine, settings)
        result = await pipeline.run()

    assert result["status"] == "completed"
    assert result["events_fetched"] == 1
    assert result["events_to_score"] == 1
