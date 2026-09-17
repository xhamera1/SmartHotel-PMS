"""Tests for the Random Forest preprocessing and temporal parameter search."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ml.features import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    build_feature_frame,
    build_feature_row,
)
from ml.pipeline import (
    RANDOM_FOREST_PARAM_DISTRIBUTIONS,
    TrainingConfig,
    build_random_forest_pipeline,
    build_randomized_search,
    tune_random_forest,
)
from ml.splitting import ExpandingWindowSplit


def feature_data(
    days: int = 24,
    *,
    start: date = date(2024, 1, 1),
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    rows: list[dict[str, object]] = []
    targets: list[float] = []
    dates: list[date] = []
    for offset in range(days):
        stay_date = start + timedelta(days=offset)
        for room_type, base_price in (("STD", 250.0), ("DLX", 420.0)):
            rows.append(
                build_feature_row(
                    stay_date=stay_date,
                    lead_time_days=30,
                    occupancy_rate=(offset % 10) / 10,
                    rooms_remaining=10 - offset % 10,
                    base_price=base_price,
                    room_type=room_type,
                    demand_indicator=offset % 101,
                    event_count_active=offset % 2,
                    max_event_score=offset % 101,
                )
            )
            targets.append(1.0 + offset / 100 + (0.05 if room_type == "DLX" else 0.0))
            dates.append(stay_date)
    return (
        build_feature_frame(rows),
        pd.Series(targets, name="price_multiplier"),
        pd.Series(dates, name="stay_date"),
    )


def test_pipeline_has_expected_preprocessing_and_deterministic_forest() -> None:
    pipeline = build_random_forest_pipeline(random_state=123, n_jobs=1)

    assert isinstance(pipeline, Pipeline)
    assert list(pipeline.named_steps) == ["preprocessor", "regressor"]
    preprocessor = pipeline.named_steps["preprocessor"]
    regressor = pipeline.named_steps["regressor"]
    assert isinstance(preprocessor, ColumnTransformer)
    assert isinstance(regressor, RandomForestRegressor)
    assert preprocessor.transformers[0][2] == list(CATEGORICAL_FEATURES)
    assert isinstance(preprocessor.transformers[0][1], OneHotEncoder)
    assert preprocessor.transformers[0][1].handle_unknown == "ignore"
    assert preprocessor.transformers[1] == ("numeric", "passthrough", list(NUMERIC_FEATURES))
    assert regressor.random_state == 123
    assert regressor.n_jobs == 1


def test_pipeline_predicts_for_unseen_room_type() -> None:
    X, y, _ = feature_data(days=8)
    pipeline = build_random_forest_pipeline(random_state=42, n_jobs=1).set_params(
        regressor__n_estimators=5
    )
    pipeline.fit(X, y)
    unseen = build_feature_frame(
        [
            build_feature_row(
                stay_date=date(2024, 2, 1),
                lead_time_days=14,
                occupancy_rate=0.5,
                rooms_remaining=2,
                base_price=700.0,
                room_type="SUI",
                demand_indicator=20,
                event_count_active=1,
                max_event_score=20,
            )
        ]
    )

    prediction = pipeline.predict(unseen)

    assert prediction.shape == (1,)
    assert np.isfinite(prediction).all()


def test_search_space_matches_planned_bounds() -> None:
    assert min(RANDOM_FOREST_PARAM_DISTRIBUTIONS["regressor__n_estimators"]) == 200
    assert max(RANDOM_FOREST_PARAM_DISTRIBUTIONS["regressor__n_estimators"]) == 600
    assert min(RANDOM_FOREST_PARAM_DISTRIBUTIONS["regressor__max_depth"]) == 8
    assert max(RANDOM_FOREST_PARAM_DISTRIBUTIONS["regressor__max_depth"]) == 24
    assert min(RANDOM_FOREST_PARAM_DISTRIBUTIONS["regressor__min_samples_leaf"]) == 1
    assert max(RANDOM_FOREST_PARAM_DISTRIBUTIONS["regressor__min_samples_leaf"]) == 20
    assert RANDOM_FOREST_PARAM_DISTRIBUTIONS["regressor__max_features"]


def test_randomized_search_fits_with_expanding_window_cv() -> None:
    X, y, dates = feature_data()
    cv = ExpandingWindowSplit(n_splits=3, validation_days=4)
    fast_parameters = {
        "regressor__n_estimators": [5],
        "regressor__max_depth": [8],
        "regressor__min_samples_leaf": [1],
        "regressor__max_features": [1.0],
    }
    search = build_randomized_search(
        cv=cv,
        n_iter=1,
        random_state=42,
        n_jobs=1,
        param_distributions=fast_parameters,
    )

    search.fit(X, y, groups=dates)

    assert isinstance(search, RandomizedSearchCV)
    assert search.cv is cv
    assert search.scoring == "neg_mean_absolute_error"
    assert isinstance(search.best_estimator_, Pipeline)
    assert search.best_params_ == {name: values[0] for name, values in fast_parameters.items()}
    assert np.isfinite(search.predict(X.tail(2))).all()


def test_tuning_never_passes_holdout_to_search(monkeypatch: pytest.MonkeyPatch) -> None:
    X, y, dates = feature_data(days=1096, start=date(2023, 1, 1))
    snapshots = pd.concat([dates, X, y], axis="columns")

    class RecordingSearch:
        def fit(
            self,
            X: pd.DataFrame,
            y: pd.Series,
            *,
            groups: pd.Series,
        ) -> RecordingSearch:
            self.X = X.copy()
            self.y = y.copy()
            self.groups = groups.copy()
            return self

    recording_search = RecordingSearch()
    monkeypatch.setattr(
        "ml.pipeline.build_randomized_search",
        lambda **_kwargs: recording_search,
    )

    result = tune_random_forest(
        snapshots,
        config=TrainingConfig(cv_splits=2, search_iterations=1),
    )

    assert len(recording_search.X) == len(result.split.X_train)
    assert len(recording_search.y) == len(result.split.y_train)
    assert recording_search.groups.max() == result.split.cutoff
    assert recording_search.groups.max() < result.split.test_dates.min()
    assert len(result.split.X_test) == 184 * 2  # Jul-Dec, 2 room types per stay date
