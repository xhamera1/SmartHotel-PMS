"""Static file event provider for tests, CI, and offline demo (D8)."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from events.models import NormalizedEvent
from events.providers.base import EventProvider

logger = logging.getLogger(__name__)

WARSAW_TZ = ZoneInfo("Europe/Warsaw")
DEFAULT_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "events" / "static_events.json"


class StaticFileEventProvider(EventProvider):
    """Load events from a committed JSON fixture file."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or DEFAULT_FIXTURE

    async def fetch_events(self) -> list[NormalizedEvent]:
        if not self._path.is_file():
            logger.warning("Static events file not found: %s", self._path)
            return []

        raw_list = json.loads(self._path.read_text(encoding="utf-8"))
        events: list[NormalizedEvent] = []
        for raw in raw_list:
            starts_at_str = raw.get("starts_at") or raw.get("startsAt")
            if not starts_at_str:
                continue
            starts_at = _parse_iso(starts_at_str)
            if starts_at is None:
                continue
            ends_at = _parse_iso(raw.get("ends_at") or raw.get("endsAt"))

            events.append(
                NormalizedEvent(
                    provider="static",
                    external_id=str(raw.get("external_id", raw.get("externalId", ""))),
                    name=str(raw.get("name", ""))[:300],
                    category=raw.get("category"),
                    venue_name=raw.get("venue_name") or raw.get("venueName"),
                    city=raw.get("city"),
                    latitude=_safe_float(raw.get("latitude") or raw.get("lat")),
                    longitude=_safe_float(raw.get("longitude") or raw.get("lon")),
                    distance_km=_safe_float(raw.get("distance_km") or raw.get("distanceKm")),
                    starts_at=starts_at,
                    ends_at=ends_at,
                    expected_attendance=_safe_int(
                        raw.get("expected_attendance") or raw.get("expectedAttendance")
                    ),
                    url=raw.get("url"),
                    raw_payload=raw,
                )
            )
        logger.info("Static provider loaded %d events from %s", len(events), self._path.name)
        return events


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(WARSAW_TZ)
    except (ValueError, TypeError):
        return None


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return None


def _safe_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return None
