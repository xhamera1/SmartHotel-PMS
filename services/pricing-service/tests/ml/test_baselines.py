"""Tests for the three RQ1 comparison baselines."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline

from ml.baselines import (
    BASELINE_LINEAR,
    BASELINE_RULE_BASED,
    BASELINE_STATIC,
    MONTH_MULTIPLIERS,
    WEEKDAY_MULTIPLIERS,
    RuleBasedPriceBaseline,
    StaticPriceBaseline,
    build_linear_regression_baseline,
    fit_baselines,
)
from ml.features import build_feature_frame, build_feature_row


def baseline_frame() -> tuple[pd.DataFrame, pd.Series]:
    rows = [
        build_feature_row(
            stay_date=date(2025, month, 3),
            lead_time_days=30,
            occupancy_rate=0.5,
            rooms_remaining=5,
            base_price=250.0,
            room_type="STD" if month % 2 else "DLX",
            demand_indicator=month * 5,
            event_count_active=0,
            max_event_score=0,
        )
        for month in range(1, 13)
    ]
    return build_feature_frame(rows), pd.Series(np.linspace(0.9, 1.5, 12))


def test_static_baseline_always_returns_base_multiplier() -> None:
    X, y = baseline_frame()
    model = StaticPriceBaseline().fit(X, y)

    assert np.array_equal(model.predict(X), np.ones(len(X)))


def test_rule_based_baseline_is_weekday_times_month_table() -> None:
    X, y = baseline_frame()
    model = RuleBasedPriceBaseline().fit(X, y)

    predicted = model.predict(X)
    expected = [
        WEEKDAY_MULTIPLIERS[int(row.day_of_week)] * MONTH_MULTIPLIERS[int(row.month) - 1]
        for row in X.itertuples(index=False)
    ]

    assert predicted == pytest.approx(expected)
    assert not np.array_equal(predicted, y.to_numpy())


def test_rule_based_baseline_rejects_invalid_calendar_values() -> None:
    X, _ = baseline_frame()
    invalid = X.copy()
    invalid["month"] = 13
    with pytest.raises(ValueError, match="month"):
        RuleBasedPriceBaseline().predict(invalid)


def test_linear_baseline_uses_shared_preprocessor() -> None:
    pipeline = build_linear_regression_baseline(n_jobs=1)

    assert isinstance(pipeline, Pipeline)
    assert isinstance(pipeline.named_steps["regressor"], LinearRegression)
    assert list(pipeline.named_steps) == ["preprocessor", "regressor"]


def test_fit_baselines_returns_complete_fitted_set() -> None:
    X, y = baseline_frame()
    models = fit_baselines(X, y)

    assert set(models) == {BASELINE_STATIC, BASELINE_RULE_BASED, BASELINE_LINEAR}
    for model in models.values():
        prediction = model.predict(X)  # type: ignore[attr-defined]
        assert len(prediction) == len(X)
        assert np.isfinite(prediction).all()
