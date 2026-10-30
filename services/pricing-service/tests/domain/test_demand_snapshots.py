"""Unit tests for demand → feature snapshot mapping (quote serving)."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from app.services.db import fetch_demand_by_dates
from domain.features_batch import DemandSnapshot


def test_fetch_demand_by_dates_uses_top_event_scores() -> None:
    """event_count_active / max_event_score come from top_event_ids + scores."""
    engine = MagicMock()
    conn = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn

    demand_mappings = MagicMock()
    demand_mappings.__iter__.return_value = iter(
        [
            {
                "date": date(2027, 6, 14),
                "indicator": 80,
                "top_event_ids": [10, 20],
            },
            {
                "date": date(2027, 6, 15),
                "indicator": 0,
                "top_event_ids": [],
            },
        ]
    )
    score_mappings = MagicMock()
    score_mappings.__iter__.return_value = iter(
        [
            {"event_id": 10, "impact_score": 55},
            {"event_id": 20, "impact_score": 90},
        ]
    )
    conn.execute.side_effect = [
        MagicMock(mappings=MagicMock(return_value=demand_mappings)),
        MagicMock(mappings=MagicMock(return_value=score_mappings)),
    ]

    result = fetch_demand_by_dates(engine, {date(2027, 6, 14), date(2027, 6, 15)})

    assert result[date(2027, 6, 14)] == DemandSnapshot(
        indicator=80, event_count_active=2, max_event_score=90
    )
    assert result[date(2027, 6, 15)] == DemandSnapshot(
        indicator=0, event_count_active=0, max_event_score=0
    )
