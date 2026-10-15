"""POST /api/v1/quotes."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.engine import Engine

from app.deps import get_engine, require_model
from app.schemas import QuotesRequest, QuotesResponse
from app.services.model_loader import ModelState
from app.services.quoting import persist_prediction_logs, quote_batch

router = APIRouter(prefix="/api/v1", tags=["Quotes"])


@router.post("/quotes", response_model=QuotesResponse)
def create_quotes(
    body: QuotesRequest,
    background_tasks: BackgroundTasks,
    engine: Engine = Depends(get_engine),
    model: ModelState = Depends(require_model),
) -> QuotesResponse:
    items, log_rows = quote_batch(
        engine=engine,
        model=model,
        request_id=body.request_id,
        items=body.items,
    )
    background_tasks.add_task(persist_prediction_logs, engine, log_rows)
    return QuotesResponse(model_version=model.version, items=items)
