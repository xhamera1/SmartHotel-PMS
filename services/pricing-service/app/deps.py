"""FastAPI dependency injection helpers."""

from __future__ import annotations

from fastapi import Request
from sqlalchemy.engine import Engine

from app.services.model_loader import ModelHolder, ModelState


def get_engine(request: Request) -> Engine:
    return request.app.state.engine


def get_model_holder(request: Request) -> ModelHolder:
    return request.app.state.model_holder


def require_model(request: Request) -> ModelState:
    from fastapi import HTTPException

    state = request.app.state.model_holder.state
    if state is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return state
