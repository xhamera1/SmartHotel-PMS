"""Health live/ready endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response, status

from app.schemas import HealthResponse
from app.services.db import check_db

router = APIRouter(tags=["Health"])


@router.get("/health/live", response_model=HealthResponse)
def live() -> HealthResponse:
    return HealthResponse(status="UP")


@router.get("/health/ready", response_model=HealthResponse)
def ready(request: Request, response: Response) -> HealthResponse:
    model_ok = request.app.state.model_holder.is_loaded
    db_ok = check_db(request.app.state.engine)
    if model_ok and db_ok:
        return HealthResponse(status="UP")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(status="DOWN")
