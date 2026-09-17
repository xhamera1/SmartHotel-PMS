"""Pandera data contracts for every emitted datagen parquet table."""

from __future__ import annotations

import pandas as pd
import pandera.pandas as pa
from pandera.typing.pandas import Series

EVENT_CATEGORIES = ("MUSIC", "SPORTS", "CONFERENCE", "CULTURE")


class CalendarSchema(pa.DataFrameModel):
    date: Series[pa.DateTime] = pa.Field(nullable=False)
    season_factor: Series[float] = pa.Field(gt=0, nullable=False)
    weekday_factor: Series[float] = pa.Field(gt=0, nullable=False)
    holiday_flag: Series[int] = pa.Field(isin=[0, 1], nullable=False)
    bridge_flag: Series[int] = pa.Field(isin=[0, 1], nullable=False)
    holiday_factor: Series[float] = pa.Field(gt=0, nullable=False)
    calendar_factor: Series[float] = pa.Field(gt=0, nullable=False)

    class Config:
        strict = True
        coerce = True
        unique = ["date"]


class EventsSchema(pa.DataFrameModel):
    event_id: Series[str] = pa.Field(nullable=False, str_length={"min_value": 1})
    category: Series[str] = pa.Field(isin=list(EVENT_CATEGORIES), nullable=False)
    name: Series[str] = pa.Field(nullable=False, str_length={"min_value": 1})
    description: Series[str] = pa.Field(nullable=False, str_length={"min_value": 1})
    start_date: Series[pa.DateTime] = pa.Field(nullable=False)
    end_date: Series[pa.DateTime] = pa.Field(nullable=False)
    attendance: Series[int] = pa.Field(gt=0, nullable=False)
    distance_km: Series[float] = pa.Field(ge=0, nullable=False)
    true_uplift: Series[float] = pa.Field(ge=0, nullable=False)

    class Config:
        strict = True
        coerce = True
        unique = ["event_id"]

    @pa.dataframe_check
    def end_on_or_after_start(cls, df: pd.DataFrame) -> pd.Series:
        return df["end_date"] >= df["start_date"]


class NightsSchema(pa.DataFrameModel):
    date: Series[pa.DateTime] = pa.Field(nullable=False)
    room_type: Series[str] = pa.Field(nullable=False, str_length={"min_value": 1})
    base_price: Series[float] = pa.Field(gt=0, nullable=False)
    demand_latent: Series[float] = pa.Field(gt=0, nullable=False)
    event_uplift: Series[float] = pa.Field(ge=0, nullable=False)
    optimal_price: Series[float] = pa.Field(gt=0, nullable=False)
    price_multiplier: Series[float] = pa.Field(gt=0, nullable=False)

    class Config:
        strict = True
        coerce = True
        unique = [["date", "room_type"]]


class BookingsSchema(pa.DataFrameModel):
    booking_id: Series[str] = pa.Field(nullable=False, str_length={"min_value": 1})
    room_type: Series[str] = pa.Field(nullable=False, str_length={"min_value": 1})
    check_in: Series[pa.DateTime] = pa.Field(nullable=False)
    check_out: Series[pa.DateTime] = pa.Field(nullable=False)
    booked_at: Series[pa.DateTime] = pa.Field(nullable=False)
    nights: Series[int] = pa.Field(ge=1, nullable=False)
    price_total: Series[float] = pa.Field(gt=0, nullable=False)
    cancelled: Series[bool] = pa.Field(nullable=False)

    class Config:
        strict = True
        coerce = True
        unique = ["booking_id"]

    @pa.dataframe_check
    def checkout_after_checkin(cls, df: pd.DataFrame) -> pd.Series:
        return df["check_out"] > df["check_in"]


class SnapshotsSchema(pa.DataFrameModel):
    stay_date: Series[pa.DateTime] = pa.Field(nullable=False)
    room_type: Series[str] = pa.Field(nullable=False, str_length={"min_value": 1})
    snapshot_date: Series[pa.DateTime] = pa.Field(nullable=False)
    lead_time_days: Series[int] = pa.Field(gt=0, nullable=False)
    occupancy_so_far: Series[float] = pa.Field(ge=0, le=1, nullable=False)
    rooms_remaining: Series[int] = pa.Field(ge=0, nullable=False)
    season_factor: Series[float] = pa.Field(gt=0, nullable=False)
    weekday_factor: Series[float] = pa.Field(gt=0, nullable=False)
    holiday_flag: Series[int] = pa.Field(isin=[0, 1], nullable=False)
    event_uplift_known: Series[float] = pa.Field(ge=0, nullable=False)
    price_multiplier: Series[float] = pa.Field(gt=0, nullable=False)

    class Config:
        strict = True
        coerce = True
        unique = [["stay_date", "room_type", "lead_time_days"]]

    @pa.dataframe_check
    def snapshot_before_stay(cls, df: pd.DataFrame) -> pd.Series:
        return df["snapshot_date"] < df["stay_date"]


DATASET_SCHEMAS: dict[str, type[pa.DataFrameModel]] = {
    "calendar": CalendarSchema,
    "events": EventsSchema,
    "nights": NightsSchema,
    "bookings": BookingsSchema,
    "snapshots": SnapshotsSchema,
}
