"""Transparent comparison baselines for the Random Forest experiment (RQ1)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Self

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline

from ml.features import FEATURE_NAMES
from ml.pipeline import build_feature_preprocessor

BASELINE_STATIC = "b0_static"
BASELINE_RULE_BASED = "b1_rule_based"
BASELINE_LINEAR = "b2_linear_regression"
RANDOM_FOREST_MODEL = "random_forest"

# A deliberately simple, pre-declared manual revenue-management table. It uses
# only weekday and broad season, never occupancy, event signals, or holdout target.
WEEKDAY_MULTIPLIERS: tuple[float, ...] = (0.90, 0.85, 0.90, 1.00, 1.15, 1.20, 1.00)
MONTH_MULTIPLIERS: tuple[float, ...] = (
    0.90,  # January
    0.90,  # February
    0.95,  # March
    1.00,  # April
    1.10,  # May
    1.20,  # June
    1.25,  # July
    1.20,  # August
    1.10,  # September
    1.00,  # October
    0.95,  # November
    1.10,  # December
)


class StaticPriceBaseline(RegressorMixin, BaseEstimator):
    """B0: always return multiplier 1.0 (the static base price)."""

    def fit(self, X: pd.DataFrame, y: object = None) -> Self:
        del y
        self.n_features_in_ = X.shape[1]
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.ones(len(X), dtype="float64")


class RuleBasedPriceBaseline(RegressorMixin, BaseEstimator):
    """B1: fixed weekday multiplier × fixed monthly season multiplier."""

    def fit(self, X: pd.DataFrame, y: object = None) -> Self:
        del y
        self._validate_columns(X)
        self.n_features_in_ = X.shape[1]
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        self._validate_columns(X)
        weekdays = pd.to_numeric(X["day_of_week"], errors="raise").to_numpy(dtype="int64")
        months = pd.to_numeric(X["month"], errors="raise").to_numpy(dtype="int64")
        if ((weekdays < 0) | (weekdays > 6)).any():
            raise ValueError("day_of_week must be in [0, 6]")
        if ((months < 1) | (months > 12)).any():
            raise ValueError("month must be in [1, 12]")
        weekday_values = np.asarray(WEEKDAY_MULTIPLIERS)[weekdays]
        month_values = np.asarray(MONTH_MULTIPLIERS)[months - 1]
        return np.asarray(weekday_values * month_values, dtype="float64")

    @staticmethod
    def _validate_columns(X: pd.DataFrame) -> None:
        missing = sorted({"day_of_week", "month"} - set(X.columns))
        if missing:
            raise ValueError(f"rule-based baseline missing columns: {missing}")


def build_linear_regression_baseline(
    *, n_jobs: int = 1, feature_names: Sequence[str] = FEATURE_NAMES
) -> Pipeline:
    """B2: ordinary least squares on exactly the same transformed features."""

    return Pipeline(
        [
            ("preprocessor", build_feature_preprocessor(feature_names=feature_names)),
            ("regressor", LinearRegression(n_jobs=n_jobs)),
        ]
    )


def fit_baselines(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    *,
    n_jobs: int = 1,
    feature_names: Sequence[str] = FEATURE_NAMES,
) -> dict[str, object]:
    """Fit all three pre-declared baselines exclusively on the train partition."""

    baselines: dict[str, object] = {
        BASELINE_STATIC: StaticPriceBaseline(),
        BASELINE_RULE_BASED: RuleBasedPriceBaseline(),
        BASELINE_LINEAR: build_linear_regression_baseline(
            n_jobs=n_jobs, feature_names=feature_names
        ),
    }
    for model in baselines.values():
        model.fit(X_train, y_train)  # type: ignore[attr-defined]
    return baselines
