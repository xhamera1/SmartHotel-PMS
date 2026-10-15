"""Tests for per-night demand aggregation."""

from __future__ import annotations

from datetime import date

from events.aggregation import (
    affected_nights_for_event,
    aggregate_demand,
    proximity_weight,
)


def test_proximity_weight_close() -> None:
    assert proximity_weight(0.0) == 1.0


def test_proximity_weight_far() -> None:
    assert proximity_weight(25.0) == 0.2


def test_proximity_weight_very_far() -> None:
    assert proximity_weight(50.0) == 0.2


def test_proximity_weight_none() -> None:
    assert proximity_weight(None) == 0.5


def test_affected_nights_single_day() -> None:
    nights = affected_nights_for_event(date(2027, 6, 14), date(2027, 6, 14), score=50)
    assert nights == [date(2027, 6, 14)]


def test_affected_nights_multi_day() -> None:
    nights = affected_nights_for_event(date(2027, 5, 12), date(2027, 5, 14), score=50)
    assert nights == [date(2027, 5, 12), date(2027, 5, 13), date(2027, 5, 14)]


def test_affected_nights_eve_for_high_score() -> None:
    nights = affected_nights_for_event(date(2027, 6, 14), date(2027, 6, 14), score=75)
    assert date(2027, 6, 13) in nights
    assert date(2027, 6, 14) in nights


def test_affected_nights_no_eve_for_low_score() -> None:
    nights = affected_nights_for_event(date(2027, 6, 14), date(2027, 6, 14), score=60)
    assert date(2027, 6, 13) not in nights


def test_aggregate_demand_single_event() -> None:
    scored = [
        {
            "event_db_id": 1,
            "impact_score": 75,
            "distance_km": 2.0,
            "affected_nights": [date(2027, 6, 14)],
        }
    ]
    result = aggregate_demand(scored)
    assert date(2027, 6, 14) in result
    assert result[date(2027, 6, 14)]["indicator"] == 75
    assert result[date(2027, 6, 14)]["top_event_ids"] == [1]


def test_aggregate_demand_overlapping_events() -> None:
    scored = [
        {
            "event_db_id": 1,
            "impact_score": 80,
            "distance_km": 2.0,
            "affected_nights": [date(2027, 6, 14)],
        },
        {
            "event_db_id": 2,
            "impact_score": 60,
            "distance_km": 5.0,
            "affected_nights": [date(2027, 6, 14)],
        },
    ]
    result = aggregate_demand(scored)
    indicator = result[date(2027, 6, 14)]["indicator"]
    # max=80, secondary=60, prox_weight(5)=0.8, 80 + 0.3*60*0.8 = 80 + 14.4 = 94
    assert indicator > 80
    assert indicator <= 100
    assert len(result[date(2027, 6, 14)]["top_event_ids"]) == 2


def test_aggregate_demand_cap_at_100() -> None:
    scored = [
        {
            "event_db_id": i,
            "impact_score": 90,
            "distance_km": 1.0,
            "affected_nights": [date(2027, 6, 14)],
        }
        for i in range(10)
    ]
    result = aggregate_demand(scored)
    assert result[date(2027, 6, 14)]["indicator"] <= 100
    assert len(result[date(2027, 6, 14)]["top_event_ids"]) <= 5


def test_aggregate_demand_multi_day_event() -> None:
    scored = [
        {
            "event_db_id": 1,
            "impact_score": 50,
            "distance_km": 3.0,
            "affected_nights": [date(2027, 5, 12), date(2027, 5, 13), date(2027, 5, 14)],
        }
    ]
    result = aggregate_demand(scored)
    assert len(result) == 3
    for d in [date(2027, 5, 12), date(2027, 5, 13), date(2027, 5, 14)]:
        assert d in result
        assert result[d]["indicator"] == 50
