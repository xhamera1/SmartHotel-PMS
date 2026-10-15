"""Heuristic fallback scorer (D9, ADR-0011)."""

from __future__ import annotations

import math
from datetime import date, timedelta

from events.models import EventScoreResult, NormalizedEvent
from events.scoring.base import EventScorer

CATEGORY_BASE: dict[str, int] = {
    "MUSIC": 60,
    "SPORTS": 55,
    "CONFERENCE": 45,
    "CULTURE": 30,
}
DEFAULT_CATEGORY_BASE = 35
DISTANCE_SCALE_KM = 15.0
ATTENDANCE_DIVISOR = 5000.0
MAX_ATTENDANCE_FACTOR = 2.0


def heuristic_score(
    *,
    category: str | None,
    expected_attendance: int | None,
    distance_km: float | None,
) -> int:
    """
    Compute a heuristic impact score.

    ``score = category_base * attendance_factor * exp(-distance_km / 15)``
    """
    base = CATEGORY_BASE.get((category or "").upper(), DEFAULT_CATEGORY_BASE)
    attendance = max(1, expected_attendance or 0)
    att_factor = min(MAX_ATTENDANCE_FACTOR, attendance / ATTENDANCE_DIVISOR)
    dist = max(0.0, distance_km if distance_km is not None else 10.0)
    decay = math.exp(-dist / DISTANCE_SCALE_KM)
    raw = base * att_factor * decay
    return max(0, min(100, round(raw)))


def _affected_nights(event: NormalizedEvent, score: int) -> list[date]:
    """Derive hotel nights from event dates; include eve for score >= 70."""
    start_date = event.starts_at.date()
    end_date = event.ends_at.date() if event.ends_at else start_date
    nights: list[date] = []
    if score >= 70:
        eve = start_date - timedelta(days=1)
        nights.append(eve)
    current = start_date
    while current <= end_date:
        nights.append(current)
        current += timedelta(days=1)
    return sorted(set(nights))


class HeuristicScorer(EventScorer):
    """Score events using a deterministic category/distance heuristic."""

    async def score(self, events: list[NormalizedEvent]) -> list[EventScoreResult]:
        results: list[EventScoreResult] = []
        for event in events:
            impact = heuristic_score(
                category=event.category,
                expected_attendance=event.expected_attendance,
                distance_km=event.distance_km,
            )
            nights = _affected_nights(event, impact)
            results.append(
                EventScoreResult(
                    event_external_id=event.external_id,
                    impact_score=impact,
                    confidence="MEDIUM",
                    affected_nights=nights,
                    rationale=(
                        f"Heuristic: {event.category or 'UNKNOWN'} category, "
                        f"~{event.expected_attendance or 0} attendance, "
                        f"{event.distance_km or 0:.1f} km away"
                    )[:240],
                    is_fallback=True,
                )
            )
        return results
