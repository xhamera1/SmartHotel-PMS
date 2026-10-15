"""GET /api/v1/demand-indicators."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.engine import Engine

from app.deps import get_engine
from app.schemas import DemandIndicatorItem, DemandIndicatorsResponse
from app.services.db import fetch_demand_range

router = APIRouter(prefix="/api/v1", tags=["Demand"])


@router.get("/demand-indicators", response_model=DemandIndicatorsResponse)
def demand_indicators(
    from_: date = Query(alias="from"),
    to: date = Query(alias="to"),
    engine: Engine = Depends(get_engine),
) -> DemandIndicatorsResponse:
    if to < from_:
        raise HTTPException(status_code=422, detail="to must be on or after from")
    rows = fetch_demand_range(engine, from_, to)
    items = [
        DemandIndicatorItem(
            date=row["date"],
            indicator=int(row["indicator"]),
            top_event_ids=list(row["top_event_ids"] or []),
        )
        for row in rows
    ]
    return DemandIndicatorsResponse(items=items)
