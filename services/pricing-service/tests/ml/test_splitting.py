"""Tests for leakage-safe temporal holdout and expanding-window CV."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from ml.features import TARGET_NAME, build_feature_row
from ml.splitting import ExpandingWindowSplit, temporal_train_test_split


def snapshot_frame(start: str, end: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for day_number, timestamp in enumerate(pd.date_range(start, end, freq="D")):
        stay_date = timestamp.date()
        for room_type, base_price in (("STD", 250.0), ("DLX", 420.0)):
            for lead_time in (30, 7):
                features = build_feature_row(
                    stay_date=stay_date,
                    lead_time_days=lead_time,
                    occupancy_rate=min(day_number % 10 / 10, 0.9),
                    rooms_remaining=10 - day_number % 10,
                    base_price=base_price,
                    room_type=room_type,
                    demand_indicator=day_number % 101,
                    event_count_active=day_number % 3,
                    max_event_score=day_number % 101,
                )
                rows.append(
                    {
                        "stay_date": stay_date,
                        "snapshot_date": stay_date - pd.Timedelta(days=lead_time),
                        **features,
                        TARGET_NAME: 1.0 + day_number / 10_000,
                    }
                )
    return pd.DataFrame(rows)


def test_temporal_holdout_is_last_six_months_without_date_overlap() -> None:
    snapshots = snapshot_frame("2023-01-01", "2025-12-31").sample(frac=1.0, random_state=7)

    split = temporal_train_test_split(snapshots)

    assert split.cutoff == pd.Timestamp("2025-06-30")
    assert split.test_start == pd.Timestamp("2025-07-01")
    assert split.train_dates.min() == pd.Timestamp("2023-01-01")
    assert split.train_dates.max() == split.cutoff
    assert split.test_dates.min() == split.test_start
    assert split.test_dates.max() == pd.Timestamp("2025-12-31")
    assert set(split.train_dates).isdisjoint(set(split.test_dates))
    assert len(split.X_train) + len(split.X_test) == len(snapshots)
    assert split.X_train.index.equals(pd.RangeIndex(len(split.X_train)))
    assert split.X_test.index.equals(pd.RangeIndex(len(split.X_test)))


def test_temporal_holdout_rejects_invalid_input() -> None:
    short_frame = snapshot_frame("2025-01-01", "2025-01-10")
    with pytest.raises(ValueError, match="no training"):
        temporal_train_test_split(short_frame, holdout_months=12)

    with pytest.raises(ValueError, match="missing required columns"):
        temporal_train_test_split(short_frame.drop(columns=["base_price"]))

    frame = snapshot_frame("2024-01-01", "2025-01-10")
    invalid_target = frame.copy()
    invalid_target.loc[0, TARGET_NAME] = np.inf
    with pytest.raises(ValueError, match="finite"):
        temporal_train_test_split(invalid_target, holdout_months=1)


def test_expanding_window_uses_complete_date_groups() -> None:
    dates = pd.Series(np.repeat(pd.date_range("2024-01-01", periods=16), 4))
    X = pd.DataFrame({"value": np.arange(len(dates))})
    splitter = ExpandingWindowSplit(n_splits=3, validation_days=3)

    folds = list(splitter.split(X, groups=dates))

    assert len(folds) == 3
    previous_train_dates: set[pd.Timestamp] = set()
    for train_indices, validation_indices in folds:
        train_dates = set(dates.iloc[train_indices])
        validation_dates = set(dates.iloc[validation_indices])
        assert len(validation_dates) == 3
        assert train_dates.isdisjoint(validation_dates)
        assert max(train_dates) < min(validation_dates)
        assert previous_train_dates.issubset(train_dates)
        for stay_date in train_dates:
            assert set(np.flatnonzero(dates.eq(stay_date))) <= set(train_indices)
        for stay_date in validation_dates:
            assert set(np.flatnonzero(dates.eq(stay_date))) <= set(validation_indices)
        previous_train_dates = train_dates


def test_expanding_window_requires_dates_and_enough_history() -> None:
    splitter = ExpandingWindowSplit(n_splits=3)
    X = pd.DataFrame({"value": range(8)})

    with pytest.raises(ValueError, match="requires stay dates"):
        list(splitter.split(X))
    with pytest.raises(ValueError, match="more than 3 unique"):
        list(splitter.split(X, groups=[date(2024, 1, 1)] * 8))
    with pytest.raises(ValueError, match="one stay date per X row"):
        list(splitter.split(X, groups=pd.date_range("2024-01-01", periods=7)))


def test_expanding_window_gap_is_measured_in_unique_dates() -> None:
    dates = pd.Series(np.repeat(pd.date_range("2024-01-01", periods=20), 2))
    X = pd.DataFrame({"value": np.arange(len(dates))})
    splitter = ExpandingWindowSplit(n_splits=2, validation_days=4, gap_days=2)

    for train_indices, validation_indices in splitter.split(X, groups=dates):
        last_train = dates.iloc[train_indices].max()
        first_validation = dates.iloc[validation_indices].min()
        assert (first_validation - last_train).days == 3
