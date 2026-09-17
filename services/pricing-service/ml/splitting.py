"""Leakage-safe temporal holdout and cross-validation splitters."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.model_selection import BaseCrossValidator, TimeSeriesSplit

from ml.features import FEATURE_NAMES, TARGET_NAME, build_feature_frame

DEFAULT_HOLDOUT_MONTHS = 6
STAY_DATE_COLUMN = "stay_date"


@dataclass(frozen=True)
class TemporalSplit:
    """Feature/target partitions with an untouched future holdout."""

    cutoff: pd.Timestamp
    test_start: pd.Timestamp
    X_train: pd.DataFrame
    y_train: pd.Series
    train_dates: pd.Series
    X_test: pd.DataFrame
    y_test: pd.Series
    test_dates: pd.Series


def _normalized_dates(values: object, *, name: str) -> pd.Series:
    try:
        dates = pd.Series(pd.to_datetime(values, errors="raise"), name=name).dt.normalize()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must contain valid dates") from exc
    if dates.isna().any():
        raise ValueError(f"{name} must not contain missing dates")
    return dates


def temporal_train_test_split(
    snapshots: pd.DataFrame,
    *,
    holdout_months: int = DEFAULT_HOLDOUT_MONTHS,
    date_column: str = STAY_DATE_COLUMN,
    target_column: str = TARGET_NAME,
) -> TemporalSplit:
    """Split snapshots into historical train data and the last N months.

    The cutoff is ``max(stay_date) - DateOffset(months=holdout_months)``. Training
    contains dates up to and including the cutoff; the test partition contains only
    later dates. No random split is ever performed and all rows for one stay date
    remain in the same partition.
    """

    if isinstance(holdout_months, bool) or not isinstance(holdout_months, int):
        raise TypeError("holdout_months must be an integer")
    if holdout_months < 1:
        raise ValueError("holdout_months must be >= 1")
    if snapshots.empty:
        raise ValueError("snapshots must not be empty")

    required = {date_column, target_column, *FEATURE_NAMES}
    missing = sorted(required - set(snapshots.columns))
    if missing:
        raise ValueError(f"snapshots missing required columns: {missing}")

    ordered = snapshots.copy()
    ordered[date_column] = _normalized_dates(ordered[date_column], name=date_column).to_numpy()
    secondary_order = [name for name in ("room_type", "lead_time_days") if name in ordered]
    ordered = ordered.sort_values([date_column, *secondary_order], kind="mergesort").reset_index(
        drop=True
    )

    maximum_date = pd.Timestamp(ordered[date_column].max())
    cutoff = (maximum_date - pd.DateOffset(months=holdout_months)).normalize()
    train_mask = ordered[date_column] <= cutoff
    test_mask = ordered[date_column] > cutoff
    if not train_mask.any():
        raise ValueError("holdout leaves no training rows")
    if not test_mask.any():
        raise ValueError("holdout leaves no test rows")

    train = ordered.loc[train_mask].reset_index(drop=True)
    test = ordered.loc[test_mask].reset_index(drop=True)
    train_dates = _normalized_dates(train[date_column], name=date_column)
    test_dates = _normalized_dates(test[date_column], name=date_column)
    if train_dates.max() >= test_dates.min():
        raise AssertionError("temporal split overlaps at the stay-date boundary")

    X_train = build_feature_frame(train.loc[:, list(FEATURE_NAMES)].to_dict(orient="records"))
    X_test = build_feature_frame(test.loc[:, list(FEATURE_NAMES)].to_dict(orient="records"))
    y_train = _target_series(train[target_column], target_column)
    y_test = _target_series(test[target_column], target_column)

    return TemporalSplit(
        cutoff=cutoff,
        test_start=pd.Timestamp(test_dates.min()),
        X_train=X_train,
        y_train=y_train,
        train_dates=train_dates,
        X_test=X_test,
        y_test=y_test,
        test_dates=test_dates,
    )


def _target_series(values: pd.Series, name: str) -> pd.Series:
    try:
        target = pd.to_numeric(values, errors="raise").astype("float64").reset_index(drop=True)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not np.isfinite(target.to_numpy()).all():
        raise ValueError(f"{name} must contain only finite values")
    if (target <= 0).any():
        raise ValueError(f"{name} must be positive")
    target.name = name
    return target


class ExpandingWindowSplit(BaseCrossValidator):
    """Expanding-window CV that keeps every stay date in exactly one side.

    ``groups`` passed to :meth:`split` must contain the stay date for every row.
    Internally sklearn's ``TimeSeriesSplit`` operates on sorted unique dates, then
    its date-level folds are expanded back to row indices. This prevents rows for
    different room types or lead times of the same hotel night crossing a boundary.
    """

    def __init__(
        self,
        n_splits: int = 5,
        *,
        validation_days: int | None = None,
        gap_days: int = 0,
    ) -> None:
        if isinstance(n_splits, bool) or not isinstance(n_splits, int) or n_splits < 2:
            raise ValueError("n_splits must be an integer >= 2")
        if validation_days is not None and (
            isinstance(validation_days, bool)
            or not isinstance(validation_days, int)
            or validation_days < 1
        ):
            raise ValueError("validation_days must be None or an integer >= 1")
        if isinstance(gap_days, bool) or not isinstance(gap_days, int) or gap_days < 0:
            raise ValueError("gap_days must be an integer >= 0")
        self.n_splits = n_splits
        self.validation_days = validation_days
        self.gap_days = gap_days

    def split(
        self,
        X: object,
        y: object = None,
        groups: object = None,
    ) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        del y
        if groups is None:
            raise ValueError("ExpandingWindowSplit requires stay dates in groups")

        dates = _normalized_dates(groups, name="groups")
        try:
            row_count = len(X)  # type: ignore[arg-type]
        except TypeError as exc:
            raise TypeError("X must be sized") from exc
        if len(dates) != row_count:
            raise ValueError("groups must have one stay date per X row")

        date_values = dates.to_numpy(dtype="datetime64[ns]")
        unique_dates = np.unique(date_values)
        if len(unique_dates) <= self.n_splits:
            raise ValueError(
                f"need more than {self.n_splits} unique stay dates; got {len(unique_dates)}"
            )

        date_splitter = TimeSeriesSplit(
            n_splits=self.n_splits,
            test_size=self.validation_days,
            gap=self.gap_days,
        )
        for train_date_indices, validation_date_indices in date_splitter.split(unique_dates):
            train_dates = unique_dates[train_date_indices]
            validation_dates = unique_dates[validation_date_indices]
            train_indices = np.flatnonzero(np.isin(date_values, train_dates))
            validation_indices = np.flatnonzero(np.isin(date_values, validation_dates))
            if date_values[train_indices].max() >= date_values[validation_indices].min():
                raise AssertionError("expanding-window fold is not strictly chronological")
            yield train_indices, validation_indices

    def get_n_splits(
        self,
        X: object = None,
        y: object = None,
        groups: object = None,
    ) -> int:
        del X, y, groups
        return self.n_splits
