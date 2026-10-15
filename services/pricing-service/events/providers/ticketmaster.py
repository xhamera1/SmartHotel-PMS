"""Ticketmaster Discovery API v2 adapter."""

from __future__ import annotations

import asyncio
import logging
import math
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from events.models import NormalizedEvent
from events.providers.base import EventProvider

logger = logging.getLogger(__name__)

WARSAW_TZ = ZoneInfo("Europe/Warsaw")
EARTH_RADIUS_KM = 6371.0
TM_BASE_URL = "https://app.ticketmaster.com/discovery/v2"
TM_PAGE_SIZE = 200
TM_MAX_PAGES = 10


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two points."""
    rlat1, rlon1, rlat2, rlon2 = (math.radians(v) for v in (lat1, lon1, lat2, lon2))
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _parse_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(WARSAW_TZ)
    except (ValueError, TypeError):
        return None


def _map_category(classifications: list[dict[str, Any]] | None) -> str | None:
    if not classifications:
        return None
    for cls in classifications:
        segment = cls.get("segment", {}).get("name", "").upper()
        if "MUSIC" in segment:
            return "MUSIC"
        if "SPORT" in segment:
            return "SPORTS"
        if "ART" in segment or "CULTURE" in segment or "THEATRE" in segment:
            return "CULTURE"
    genre = classifications[0].get("genre", {}).get("name", "")
    if genre:
        return genre.upper()[:50]
    return None


class TicketmasterProvider(EventProvider):
    """Fetch events from the Ticketmaster Discovery API v2."""

    def __init__(
        self,
        *,
        api_key: str,
        hotel_lat: float,
        hotel_lon: float,
        radius_km: float = 15.0,
        horizon_days: int = 120,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("Ticketmaster API key is required")
        self._api_key = api_key
        self._lat = hotel_lat
        self._lon = hotel_lon
        self._radius_km = radius_km
        self._horizon_days = horizon_days
        self._client = client
        self._semaphore = asyncio.Semaphore(5)

    async def fetch_events(self) -> list[NormalizedEvent]:
        now = datetime.now(WARSAW_TZ)
        start = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_dt = now + timedelta(days=self._horizon_days)
        end = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        params: dict[str, Any] = {
            "apikey": self._api_key,
            "latlong": f"{self._lat},{self._lon}",
            "radius": str(int(self._radius_km)),
            "unit": "km",
            "startDateTime": start,
            "endDateTime": end,
            "size": str(TM_PAGE_SIZE),
            "sort": "date,asc",
        }

        events: list[NormalizedEvent] = []
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=30.0)
        try:
            for page in range(TM_MAX_PAGES):
                params["page"] = str(page)
                raw_events = await self._fetch_page(client, params)
                if raw_events is None:
                    break
                for raw in raw_events:
                    event = self._map_event(raw)
                    if event is not None:
                        events.append(event)
                page_info = raw_events[0].get("_page", {}) if raw_events else {}
                total_pages = page_info.get("totalPages", 1) if isinstance(page_info, dict) else 1
                if page + 1 >= total_pages:
                    break
        finally:
            if owns_client:
                await client.aclose()

        logger.info("Ticketmaster fetched %d events within %d km", len(events), self._radius_km)
        return events

    async def _fetch_page(
        self, client: httpx.AsyncClient, params: dict[str, Any]
    ) -> list[dict[str, Any]] | None:
        async with self._semaphore:
            for attempt in range(4):
                try:
                    resp = await client.get(f"{TM_BASE_URL}/events.json", params=params)
                    if resp.status_code == 429:
                        wait = 2**attempt
                        logger.warning("Ticketmaster 429 — backing off %ds", wait)
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    embedded = data.get("_embedded", {})
                    return embedded.get("events", [])  # type: ignore[no-any-return]
                except httpx.HTTPStatusError:
                    logger.exception("Ticketmaster HTTP error on page %s", params.get("page"))
                    return None
                except Exception:
                    logger.exception("Ticketmaster request failed on page %s", params.get("page"))
                    if attempt == 3:
                        return None
                    await asyncio.sleep(2**attempt)
        return None

    def _map_event(self, raw: dict[str, Any]) -> NormalizedEvent | None:
        event_id = raw.get("id", "")
        name = raw.get("name", "")
        if not event_id or not name:
            return None

        dates = raw.get("dates", {})
        start_obj = dates.get("start", {})
        starts_at = _parse_datetime(start_obj.get("dateTime"))
        if starts_at is None:
            return None

        end_obj = dates.get("end", {})
        ends_at = _parse_datetime(end_obj.get("dateTime"))

        venues = (raw.get("_embedded", {}) or {}).get("venues", [])
        venue = venues[0] if venues else {}
        venue_name = venue.get("name")
        city = (venue.get("city") or {}).get("name")
        location = venue.get("location", {})
        lat = _safe_float(location.get("latitude"))
        lon = _safe_float(location.get("longitude"))

        distance_km: float | None = None
        if lat is not None and lon is not None:
            distance_km = round(haversine(self._lat, self._lon, lat, lon), 2)
            if distance_km > self._radius_km * 1.5:
                return None

        attendance: int | None = None
        if "seatmap" in raw:
            attendance = _safe_int(raw.get("seatmap", {}).get("totalCapacity"))
        if attendance is None:
            for price_range in raw.get("priceRanges", []):
                cap = _safe_int(price_range.get("max"))
                if cap and (attendance is None or cap > attendance):
                    attendance = cap

        category = _map_category(raw.get("classifications"))

        return NormalizedEvent(
            provider="ticketmaster",
            external_id=str(event_id),
            name=name[:300],
            category=category,
            venue_name=venue_name[:200] if venue_name else None,
            city=city[:100] if city else None,
            latitude=lat,
            longitude=lon,
            distance_km=distance_km,
            starts_at=starts_at,
            ends_at=ends_at,
            expected_attendance=attendance,
            url=raw.get("url"),
            raw_payload=raw,
        )


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
