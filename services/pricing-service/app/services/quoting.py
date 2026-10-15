"""Batch quote prediction service."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from app.schemas import QuoteItemRequest, QuoteItemResponse
from app.services.db import fetch_demand_by_dates, insert_prediction_logs
from app.services.model_loader import ModelState
from domain.factors import build_factors
from domain.features_batch import QuoteFeatureInput, build_feature_frame_from_batch
from domain.pricing import clamp_and_round


def quote_batch(
    *,
    engine: sa.Engine,
    model: ModelState,
    request_id: UUID,
    items: list[QuoteItemRequest],
) -> tuple[list[QuoteItemResponse], list[dict[str, Any]]]:
    feature_inputs = [
        QuoteFeatureInput(
            stay_date=item.date,
            room_type=item.room_type_code,
            base_price=float(item.base_price),
            occupancy_rate=float(item.occupancy_rate),
            rooms_remaining=int(item.rooms_remaining),
            lead_time_days=int(item.lead_time_days),
        )
        for item in items
    ]
    dates = {item.stay_date for item in feature_inputs}
    demand = fetch_demand_by_dates(engine, dates)
    frame = build_feature_frame_from_batch(feature_inputs, demand)
    predictions = model.pipeline.predict(frame)

    responses: list[QuoteItemResponse] = []
    log_rows: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        raw_multiplier = float(predictions[index])
        price, served_multiplier = clamp_and_round(
            base_price=float(item.base_price),
            multiplier=raw_multiplier,
            min_price=float(item.min_price),
            max_price=float(item.max_price),
        )
        stay: date = item.date
        snap = demand.get(stay)
        indicator = int(snap.indicator) if snap else 0
        is_weekend = bool(frame.loc[index, "is_weekend"])
        factors = build_factors(
            demand_indicator=indicator,
            occupancy_rate=float(item.occupancy_rate),
            is_weekend=is_weekend,
            top_signals=model.top_signals,
        )
        feature_payload = {name: _jsonable(frame.loc[index, name]) for name in frame.columns}
        responses.append(
            QuoteItemResponse(
                room_type_code=item.room_type_code,
                date=item.date,
                price=price,
                multiplier=served_multiplier,
                demand_indicator=indicator,
                factors=factors,
                model_version=model.version,
            )
        )
        log_rows.append(
            {
                "request_id": str(request_id),
                "room_type_code": item.room_type_code,
                "stay_date": item.date,
                "features": feature_payload,
                "multiplier": served_multiplier,
                "price": str(price),
                "model_version": model.version,
            }
        )
    return responses, log_rows


def persist_prediction_logs(engine: sa.Engine, rows: list[dict[str, Any]]) -> None:
    insert_prediction_logs(engine, rows)


def _jsonable(value: object) -> object:
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
