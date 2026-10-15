"""GET /api/v1/model."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas import ModelInfoResponse

router = APIRouter(prefix="/api/v1", tags=["Model"])


@router.get("/model", response_model=ModelInfoResponse)
def model_info(request: Request) -> ModelInfoResponse:
    state = request.app.state.model_holder.state
    if state is None:
        return ModelInfoResponse(
            version="",
            trained_at="",
            feature_schema_hash="",
            metrics={},
            is_ready=False,
        )
    return ModelInfoResponse(
        version=state.version,
        trained_at=state.trained_at,
        feature_schema_hash=state.feature_schema_hash,
        metrics=state.metrics,
        is_ready=True,
    )
