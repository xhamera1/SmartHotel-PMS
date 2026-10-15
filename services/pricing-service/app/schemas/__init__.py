"""API request/response schemas (camelCase JSON, extra=forbid)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


class ApiModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        alias_generator=_to_camel,
    )


class QuoteItemRequest(ApiModel):
    room_type_code: str = Field(min_length=1, max_length=30)
    date: date
    base_price: Decimal = Field(gt=0)
    min_price: Decimal = Field(gt=0)
    max_price: Decimal = Field(gt=0)
    occupancy_rate: float = Field(ge=0, le=1)
    rooms_remaining: int = Field(ge=0)
    lead_time_days: int = Field(ge=0)

    @model_validator(mode="after")
    def price_band(self) -> QuoteItemRequest:
        if self.min_price > self.max_price:
            raise ValueError("maxPrice must be >= minPrice")
        if not (self.min_price <= self.base_price <= self.max_price):
            raise ValueError("basePrice must lie within [minPrice, maxPrice]")
        return self


class QuotesRequest(ApiModel):
    request_id: UUID
    currency: Literal["PLN"] = "PLN"
    items: list[QuoteItemRequest] = Field(min_length=1, max_length=400)


class QuoteItemResponse(ApiModel):
    room_type_code: str
    date: date
    price: Decimal
    multiplier: float
    demand_indicator: int
    factors: dict[str, Any]
    model_version: str


class QuotesResponse(ApiModel):
    model_version: str
    items: list[QuoteItemResponse]


class DemandIndicatorItem(ApiModel):
    date: date
    indicator: int
    top_event_ids: list[int] = Field(default_factory=list)


class DemandIndicatorsResponse(ApiModel):
    items: list[DemandIndicatorItem]


class EventItem(ApiModel):
    id: int
    name: str
    category: str | None = None
    starts_at: str
    ends_at: str | None = None
    impact_score: int | None = None
    distance_km: float | None = None


class EventsResponse(ApiModel):
    items: list[EventItem]


class ModelInfoResponse(ApiModel):
    version: str
    trained_at: str
    feature_schema_hash: str
    metrics: dict[str, Any]
    is_ready: bool


class EventsSyncResponse(ApiModel):
    status: str
    detail: str


class HealthResponse(ApiModel):
    status: str
