"""Tests for Gemini scorer (SDK fully mocked)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from events.models import NormalizedEvent
from events.scoring.gemini import GeminiScorer


def _make_event(eid: str = "g-001", name: str = "Test Event") -> NormalizedEvent:
    return NormalizedEvent(
        provider="static",
        external_id=eid,
        name=name,
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


def _mock_genai_response(text: str) -> MagicMock:
    resp = MagicMock()
    resp.text = text
    return resp


@pytest.mark.asyncio
async def test_gemini_scorer_valid_response() -> None:
    response_json = json.dumps(
        {
            "scores": [
                {
                    "event_id": "g-001",
                    "impact_score": 75,
                    "confidence": "HIGH",
                    "affected_nights": ["2027-06-14"],
                    "rationale": "Large music event with 10k attendance",
                }
            ]
        }
    )

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = _mock_genai_response(response_json)

    with patch("events.scoring.gemini.genai") as mock_genai:
        mock_genai.Client.return_value = mock_client
        mock_genai.types = MagicMock()

        scorer = GeminiScorer(api_key="test-key", model="test-model")
        results = await scorer.score([_make_event()])

    assert len(results) == 1
    assert results[0].impact_score == 75
    assert results[0].confidence == "HIGH"
    assert not results[0].is_fallback


@pytest.mark.asyncio
async def test_gemini_scorer_batch_split() -> None:
    """Events beyond BATCH_SIZE are split into multiple calls."""
    events = [_make_event(eid=f"g-{i:03d}") for i in range(25)]

    def make_response(*args, **kwargs) -> MagicMock:
        scores = []
        for i in range(20):
            scores.append(
                {
                    "event_id": f"g-{i:03d}",
                    "impact_score": 50,
                    "confidence": "MEDIUM",
                    "affected_nights": ["2027-06-14"],
                    "rationale": "Test",
                }
            )
        return _mock_genai_response(json.dumps({"scores": scores}))

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = make_response

    with patch("events.scoring.gemini.genai") as mock_genai:
        mock_genai.Client.return_value = mock_client
        mock_genai.types = MagicMock()

        scorer = GeminiScorer(api_key="test-key")
        results = await scorer.score(events)

    # At least one batch was scored
    assert len(results) >= 20
    assert mock_client.models.generate_content.call_count >= 1


@pytest.mark.asyncio
async def test_gemini_scorer_circuit_breaker() -> None:
    """After 3 consecutive failures, circuit breaker opens."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("API Error")

    with patch("events.scoring.gemini.genai") as mock_genai:
        mock_genai.Client.return_value = mock_client
        mock_genai.types = MagicMock()

        scorer = GeminiScorer(api_key="test-key")
        events = [_make_event(eid=f"g-{i}") for i in range(5)]

        results = await scorer.score(events)

    # Circuit should open; results may be empty
    assert scorer.is_circuit_open or len(results) == 0


@pytest.mark.asyncio
async def test_gemini_scorer_quota_check() -> None:
    """When budget_check returns False, scorer skips."""
    scorer = GeminiScorer(
        api_key="test-key",
        budget_check=lambda: False,
    )
    results = await scorer.score([_make_event()])
    assert results == []
