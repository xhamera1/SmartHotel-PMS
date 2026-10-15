"""Per-night demand aggregation from scored events."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, timedelta

import sqlalchemy as sa

logger = logging.getLogger(__name__)

EVE_THRESHOLD = 70
SECONDARY_WEIGHT = 0.3
TOP_EVENT_LIMIT = 5


def proximity_weight(distance_km: float | None) -> float:
    """``clamp(1 - distance_km/25, 0.2, 1.0)``."""
    if distance_km is None:
        return 0.5
    raw = 1.0 - (distance_km / 25.0)
    return max(0.2, min(1.0, raw))


def affected_nights_for_event(
    starts_at_date: date,
    ends_at_date: date | None,
    score: int,
) -> list[date]:
    """Derive hotel nights including the eve-night rule for high scores."""
    end = ends_at_date or starts_at_date
    nights: list[date] = []
    if score >= EVE_THRESHOLD:
        nights.append(starts_at_date - timedelta(days=1))
    current = starts_at_date
    while current <= end:
        nights.append(current)
        current += timedelta(days=1)
    return sorted(set(nights))


def aggregate_demand(
    scored_events: list[dict],
) -> dict[date, dict]:
    """
    Aggregate scored events into per-night demand indicators.

    Each dict in ``scored_events`` must have:
      event_db_id, impact_score, distance_km, affected_nights (list[date])

    Returns ``{date: {"indicator": int, "top_event_ids": list[int]}}``
    """
    night_events: dict[date, list[dict]] = defaultdict(list)
    for ev in scored_events:
        for night in ev.get("affected_nights", []):
            if isinstance(night, str):
                night = date.fromisoformat(night)
            night_events[night].append(ev)

    result: dict[date, dict] = {}
    for night, events in night_events.items():
        sorted_events = sorted(events, key=lambda e: e["impact_score"], reverse=True)
        max_score = sorted_events[0]["impact_score"]
        secondary_sum = 0.0
        for ev in sorted_events[1:]:
            weight = proximity_weight(ev.get("distance_km"))
            secondary_sum += ev["impact_score"] * weight

        indicator = min(100, round(max_score + SECONDARY_WEIGHT * secondary_sum))
        top_ids = [ev["event_db_id"] for ev in sorted_events[:TOP_EVENT_LIMIT]]

        result[night] = {
            "indicator": indicator,
            "top_event_ids": top_ids,
        }

    return result


def upsert_daily_demand(engine: sa.Engine, demand: dict[date, dict]) -> int:
    """Upsert aggregated demand into ``pricing.daily_demand``. Returns count."""
    if not demand:
        return 0

    upsert = sa.text(
        """
        INSERT INTO pricing.daily_demand (date, indicator, top_event_ids)
        VALUES (:date, :indicator, :top_event_ids)
        ON CONFLICT (date) DO UPDATE SET
            indicator = EXCLUDED.indicator,
            top_event_ids = EXCLUDED.top_event_ids,
            computed_at = now()
        """
    )

    with engine.begin() as conn:
        for day, data in demand.items():
            conn.execute(
                upsert,
                {
                    "date": day,
                    "indicator": data["indicator"],
                    "top_event_ids": data["top_event_ids"],
                },
            )

    logger.info("Upserted demand for %d nights", len(demand))
    return len(demand)
