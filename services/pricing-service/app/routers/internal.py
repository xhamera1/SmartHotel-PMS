"""Operational internal endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas import EventsSyncResponse, HealthResponse
from app.services.model_loader import load_active_model

router = APIRouter(prefix="/internal", tags=["Internal"])


@router.post("/model/reload", response_model=HealthResponse)
def reload_model(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    state = load_active_model(
        request.app.state.engine,
        fixture_dir=settings.model_artifact_dir,
        allow_fixture=settings.allow_fixture_model,
    )
    request.app.state.model_holder.set(state)
    if state is None:
        return HealthResponse(status="DOWN")
    return HealthResponse(status="UP")


@router.post("/events/sync", response_model=EventsSyncResponse, status_code=202)
def sync_events() -> EventsSyncResponse:
    return EventsSyncResponse(
        status="accepted",
        detail="Event sync is implemented in Phase 7; no-op stub in Phase 6",
    )
