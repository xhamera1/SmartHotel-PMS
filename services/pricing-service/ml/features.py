"""Canonical feature contract and feature construction for pricing ML.

This module is intentionally independent of ``datagen`` and the future API layer.
Those producers must call :func:`build_feature_row` instead of reimplementing
calendar logic or choosing their own column names and dtypes.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Literal

import holidays
import pandas as pd

FeatureDtype = Literal["int64", "float64", "bool", "category"]


@dataclass(frozen=True)
class FeatureSpec:
    """One ordered feature-column definition used in compatibility checks."""

    name: str
    dtype: FeatureDtype


# Order is part of the persisted model contract. Additions, removals, reordering,
# or dtype changes deliberately produce a different FEATURE_SCHEMA_HASH.
FEATURE_SCHEMA: tuple[FeatureSpec, ...] = (
    FeatureSpec("day_of_week", "int64"),
    FeatureSpec("month", "int64"),
    FeatureSpec("week_of_year", "int64"),
    FeatureSpec("is_weekend", "bool"),
    FeatureSpec("is_holiday", "bool"),
    FeatureSpec("is_holiday_adjacent", "bool"),
    FeatureSpec("lead_time_days", "int64"),
    FeatureSpec("occupancy_rate", "float64"),
    FeatureSpec("rooms_remaining", "int64"),
    FeatureSpec("base_price", "float64"),
    FeatureSpec("room_type", "category"),
    FeatureSpec("demand_indicator", "int64"),
    FeatureSpec("event_count_active", "int64"),
    FeatureSpec("max_event_score", "int64"),
)

TARGET_NAME = "price_multiplier"
TARGET_DTYPE = "float64"

FEATURE_NAMES: tuple[str, ...] = tuple(spec.name for spec in FEATURE_SCHEMA)
FEATURE_DTYPES: dict[str, FeatureDtype] = {spec.name: spec.dtype for spec in FEATURE_SCHEMA}
CATEGORICAL_FEATURES: tuple[str, ...] = tuple(
    spec.name for spec in FEATURE_SCHEMA if spec.dtype == "category"
)
BOOLEAN_FEATURES: tuple[str, ...] = tuple(
    spec.name for spec in FEATURE_SCHEMA if spec.dtype == "bool"
)
NUMERIC_FEATURES: tuple[str, ...] = tuple(
    spec.name for spec in FEATURE_SCHEMA if spec.dtype in {"int64", "float64", "bool"}
)


def feature_schema_payload(
    schema: Iterable[FeatureSpec] = FEATURE_SCHEMA,
) -> list[dict[str, str]]:
    """Return the JSON-safe ordered representation persisted in metadata."""

    return [asdict(spec) for spec in schema]


def compute_feature_schema_hash(schema: Iterable[FeatureSpec] = FEATURE_SCHEMA) -> str:
    """SHA-256 over canonical JSON containing feature names, dtypes, and order."""

    payload = json.dumps(
        feature_schema_payload(schema),
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


FEATURE_SCHEMA_HASH = compute_feature_schema_hash()


def _as_date(value: date | datetime | pd.Timestamp) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise TypeError("stay_date must be a date or datetime")


@lru_cache(maxsize=64)
def _polish_holidays(years: tuple[int, ...]) -> frozenset[date]:
    return frozenset(holidays.country_holidays("PL", years=years).keys())


def calendar_features(stay_date: date | datetime | pd.Timestamp) -> dict[str, int | bool]:
    """Build deterministic calendar features for one Polish hotel night.

    ``day_of_week`` uses Python's stable Monday=0 ... Sunday=6 convention and
    ``week_of_year`` is the ISO-8601 week number. A holiday-adjacent day is a
    non-holiday directly before or after a Polish public holiday.
    """

    day = _as_date(stay_date)
    # Neighbour lookup at New Year needs both surrounding calendar years.
    holiday_dates = _polish_holidays((day.year - 1, day.year, day.year + 1))
    is_holiday = day in holiday_dates
    is_adjacent = not is_holiday and (
        day - timedelta(days=1) in holiday_dates or day + timedelta(days=1) in holiday_dates
    )
    return {
        "day_of_week": day.weekday(),
        "month": day.month,
        "week_of_year": day.isocalendar().week,
        "is_weekend": day.weekday() >= 5,
        "is_holiday": is_holiday,
        "is_holiday_adjacent": is_adjacent,
    }


def _require_int(name: str, value: int, *, minimum: int, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        bounds = f"[{minimum}, {maximum}]" if maximum is not None else f">= {minimum}"
        raise ValueError(f"{name} must be {bounds}")
    return value


def _require_finite_float(
    name: str,
    value: float,
    *,
    minimum: float,
    maximum: float | None = None,
    strict_minimum: bool = False,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    result = float(value)
    below = result <= minimum if strict_minimum else result < minimum
    if not math.isfinite(result) or below or (maximum is not None and result > maximum):
        lower = f"> {minimum}" if strict_minimum else f">= {minimum}"
        upper = f" and <= {maximum}" if maximum is not None else ""
        raise ValueError(f"{name} must be finite, {lower}{upper}")
    return result


def build_feature_row(
    *,
    stay_date: date | datetime | pd.Timestamp,
    lead_time_days: int,
    occupancy_rate: float,
    rooms_remaining: int,
    base_price: float,
    room_type: str,
    demand_indicator: int,
    event_count_active: int,
    max_event_score: int,
) -> dict[str, object]:
    """Build and validate one model input in canonical schema order."""

    if not isinstance(room_type, str) or not room_type.strip():
        raise ValueError("room_type must be a non-empty string")

    values: dict[str, object] = {
        **calendar_features(stay_date),
        "lead_time_days": _require_int("lead_time_days", lead_time_days, minimum=0),
        "occupancy_rate": _require_finite_float(
            "occupancy_rate", occupancy_rate, minimum=0.0, maximum=1.0
        ),
        "rooms_remaining": _require_int("rooms_remaining", rooms_remaining, minimum=0),
        "base_price": _require_finite_float(
            "base_price", base_price, minimum=0.0, strict_minimum=True
        ),
        "room_type": room_type.strip(),
        "demand_indicator": _require_int(
            "demand_indicator", demand_indicator, minimum=0, maximum=100
        ),
        "event_count_active": _require_int("event_count_active", event_count_active, minimum=0),
        "max_event_score": _require_int("max_event_score", max_event_score, minimum=0, maximum=100),
    }
    return {name: values[name] for name in FEATURE_NAMES}


def build_feature_frame(rows: Iterable[Mapping[str, object]]) -> pd.DataFrame:
    """Create a DataFrame with exact model column order and pandas dtypes.

    This is the common finalization boundary for training and serving. It rejects
    missing or additional values so silent train/serve skew cannot pass through.
    """

    materialized = list(rows)
    for index, row in enumerate(materialized):
        actual = set(row)
        expected = set(FEATURE_NAMES)
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            raise ValueError(f"feature row {index}: missing={missing}, extra={extra}")

    if not materialized:
        return pd.DataFrame(
            {spec.name: pd.Series(dtype=spec.dtype) for spec in FEATURE_SCHEMA},
            columns=FEATURE_NAMES,
        )

    frame = pd.DataFrame(materialized, columns=FEATURE_NAMES)
    return frame.astype(FEATURE_DTYPES)
