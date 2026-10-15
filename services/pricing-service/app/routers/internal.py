"""Operational internal endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Request

from app.schemas import EventsSyncResponse, HealthResponse
from app.services.model_loader import load_active_model
from app.settings import DEFAULT_FIXTURE_MODEL

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["Internal"])


@router.post("/model/reload", response_model=HealthResponse)
def reload_model(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    state = load_active_model(
        request.app.state.engine,
        fixture_dir=DEFAULT_FIXTURE_MODEL,
        allow_fixture=settings.allow_fixture_model,
    )
    request.app.state.model_holder.set(state)
    if state is None:
        return HealthResponse(status="DOWN")
    return HealthResponse(status="UP")


async def _run_event_sync(engine, settings) -> None:  # noqa: ANN001
    """Background task: run the full event sync pipeline."""
    try:
        from events.sync import run_sync

        result = await run_sync(engine, settings)
        logger.info("Event sync completed: %s", result)
    except Exception:
        logger.exception("Event sync failed")


@router.post("/events/sync", response_model=EventsSyncResponse, status_code=202)
async def sync_events(
    request: Request,
    background_tasks: BackgroundTasks,
) -> EventsSyncResponse:
    engine = request.app.state.engine
    settings = request.app.state.settings

    if engine is None:
        return EventsSyncResponse(
            status="rejected",
            detail="Database not available",
        )

    background_tasks.add_task(_run_event_sync, engine, settings)
    return EventsSyncResponse(
        status="accepted",
        detail="Event sync pipeline started in background",
    )
