"""Contract tests for the shared train/serve feature module."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from ml.features import (
    BOOLEAN_FEATURES,
    CATEGORICAL_FEATURES,
    FEATURE_NAMES,
    FEATURE_SCHEMA,
    FEATURE_SCHEMA_HASH,
    NUMERIC_FEATURES,
    FeatureSpec,
    build_feature_frame,
    build_feature_row,
    calendar_features,
    compute_feature_schema_hash,
    feature_schema_payload,
)


def _valid_row(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "stay_date": date(2024, 5, 4),
        "lead_time_days": 30,
        "occupancy_rate": 0.75,
        "rooms_remaining": 5,
        "base_price": 250.0,
        "room_type": "STD",
        "demand_indicator": 62,
        "event_count_active": 2,
        "max_event_score": 55,
    }
    values.update(overrides)
    return build_feature_row(**values)  # type: ignore[arg-type]


def test_feature_schema_has_expected_names_dtypes_and_order() -> None:
    assert feature_schema_payload() == [
        {"name": "day_of_week", "dtype": "int64"},
        {"name": "month", "dtype": "int64"},
        {"name": "week_of_year", "dtype": "int64"},
        {"name": "is_weekend", "dtype": "bool"},
        {"name": "is_holiday", "dtype": "bool"},
        {"name": "is_holiday_adjacent", "dtype": "bool"},
        {"name": "lead_time_days", "dtype": "int64"},
        {"name": "occupancy_rate", "dtype": "float64"},
        {"name": "rooms_remaining", "dtype": "int64"},
        {"name": "base_price", "dtype": "float64"},
        {"name": "room_type", "dtype": "category"},
        {"name": "demand_indicator", "dtype": "int64"},
        {"name": "event_count_active", "dtype": "int64"},
        {"name": "max_event_score", "dtype": "int64"},
    ]
    assert tuple(item["name"] for item in feature_schema_payload()) == FEATURE_NAMES
    assert CATEGORICAL_FEATURES == ("room_type",)
    assert set(BOOLEAN_FEATURES) == {"is_weekend", "is_holiday", "is_holiday_adjacent"}
    assert set(FEATURE_NAMES) == set(NUMERIC_FEATURES) | set(CATEGORICAL_FEATURES)


def test_feature_schema_hash_is_stable_and_order_sensitive() -> None:
    assert compute_feature_schema_hash() == FEATURE_SCHEMA_HASH
    assert FEATURE_SCHEMA_HASH == "6a428877c2f519adb20b53964ab287659be8ddb8f1092c93b43ab884bb9ec449"
    assert len(FEATURE_SCHEMA_HASH) == 64
    reversed_schema = tuple(reversed(FEATURE_SCHEMA))
    assert compute_feature_schema_hash(reversed_schema) != FEATURE_SCHEMA_HASH
    changed_dtype = (*FEATURE_SCHEMA[:-1], FeatureSpec("max_event_score", "float64"))
    assert compute_feature_schema_hash(changed_dtype) != FEATURE_SCHEMA_HASH


def test_calendar_features_use_iso_calendar_and_polish_holidays() -> None:
    holiday = calendar_features(date(2024, 5, 1))
    adjacent = calendar_features(date(2024, 4, 30))
    saturday = calendar_features(date(2024, 5, 4))

    assert holiday == {
        "day_of_week": 2,
        "month": 5,
        "week_of_year": 18,
        "is_weekend": False,
        "is_holiday": True,
        "is_holiday_adjacent": False,
    }
    assert adjacent["is_holiday_adjacent"] is True
    assert saturday["is_weekend"] is True


def test_build_feature_frame_enforces_order_and_dtypes() -> None:
    row = _valid_row()
    assert tuple(row) == FEATURE_NAMES

    frame = build_feature_frame([row])
    assert tuple(frame.columns) == FEATURE_NAMES
    assert str(frame.dtypes["room_type"]) == "category"
    assert str(frame.dtypes["occupancy_rate"]) == "float64"
    assert str(frame.dtypes["is_weekend"]) == "bool"
    assert str(frame.dtypes["demand_indicator"]) == "int64"

    empty = build_feature_frame([])
    assert tuple(empty.columns) == FEATURE_NAMES
    assert empty.empty
    assert str(empty.dtypes["room_type"]) == "category"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("lead_time_days", -1),
        ("occupancy_rate", 1.01),
        ("rooms_remaining", -1),
        ("base_price", 0.0),
        ("room_type", ""),
        ("demand_indicator", 101),
        ("event_count_active", -1),
        ("max_event_score", -1),
    ],
)
def test_build_feature_row_rejects_out_of_contract_values(field: str, value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _valid_row(**{field: value})


def test_build_feature_frame_rejects_schema_drift() -> None:
    row = _valid_row()
    row["unexpected"] = 1
    with pytest.raises(ValueError, match="extra=.*unexpected"):
        build_feature_frame([row])

    missing = _valid_row()
    del missing["month"]
    with pytest.raises(ValueError, match="missing=.*month"):
        build_feature_frame([missing])


def test_timestamp_is_accepted_as_stay_date() -> None:
    row = _valid_row(stay_date=pd.Timestamp("2024-05-04"))
    assert row["day_of_week"] == 5
