"""GET /api/v1/events."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.engine import Engine

from app.deps import get_engine
from app.schemas import EventItem, EventsResponse
from app.services.db import fetch_events_range

router = APIRouter(prefix="/api/v1", tags=["Events"])


@router.get("/events", response_model=EventsResponse)
def list_events(
    from_: date = Query(alias="from"),
    to: date = Query(alias="to"),
    engine: Engine = Depends(get_engine),
) -> EventsResponse:
    if to < from_:
        raise HTTPException(status_code=422, detail="to must be on or after from")
    rows = fetch_events_range(engine, from_, to)
    items = [
        EventItem(
            id=int(row["id"]),
            name=str(row["name"]),
            category=row["category"],
            starts_at=row["starts_at"].isoformat()
            if hasattr(row["starts_at"], "isoformat")
            else str(row["starts_at"]),
            ends_at=row["ends_at"].isoformat()
            if row["ends_at"] is not None and hasattr(row["ends_at"], "isoformat")
            else (str(row["ends_at"]) if row["ends_at"] is not None else None),
            impact_score=int(row["impact_score"]) if row["impact_score"] is not None else None,
            distance_km=float(row["distance_km"]) if row["distance_km"] is not None else None,
        )
        for row in rows
    ]
    return EventsResponse(items=items)
