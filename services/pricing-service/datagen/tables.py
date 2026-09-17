"""Column contracts for datagen parquet outputs (filled in later Phase 4 steps)."""

from __future__ import annotations

import pandas as pd

EVENTS_COLUMNS: dict[str, str] = {
    "event_id": "string",
    "category": "string",
    "name": "string",
    "description": "string",
    "start_date": "datetime64[ns]",
    "end_date": "datetime64[ns]",
    "attendance": "int64",
    "distance_km": "float64",
    "true_uplift": "float64",
}

NIGHTS_COLUMNS: dict[str, str] = {
    "date": "datetime64[ns]",
    "room_type": "string",
    "base_price": "float64",
    "demand_latent": "float64",
    "event_uplift": "float64",
    "optimal_price": "float64",
    "price_multiplier": "float64",
}

BOOKINGS_COLUMNS: dict[str, str] = {
    "booking_id": "string",
    "room_type": "string",
    "check_in": "datetime64[ns]",
    "check_out": "datetime64[ns]",
    "booked_at": "datetime64[ns]",
    "nights": "int64",
    "price_total": "float64",
    "cancelled": "bool",
}

SNAPSHOTS_COLUMNS: dict[str, str] = {
    "stay_date": "datetime64[ns]",
    "room_type": "string",
    "snapshot_date": "datetime64[ns]",
    "lead_time_days": "int64",
    "occupancy_so_far": "float64",
    "rooms_remaining": "int64",
    "season_factor": "float64",
    "weekday_factor": "float64",
    "holiday_flag": "int64",
    "event_uplift_known": "float64",
    "price_multiplier": "float64",
}

DATASET_NAMES = ("events", "nights", "bookings", "snapshots")


def empty_frame(columns: dict[str, str]) -> pd.DataFrame:
    frame = pd.DataFrame({name: pd.Series(dtype=dtype) for name, dtype in columns.items()})
    return frame


def empty_datasets() -> dict[str, pd.DataFrame]:
    return {
        "events": empty_frame(EVENTS_COLUMNS),
        "nights": empty_frame(NIGHTS_COLUMNS),
        "bookings": empty_frame(BOOKINGS_COLUMNS),
        "snapshots": empty_frame(SNAPSHOTS_COLUMNS),
    }
