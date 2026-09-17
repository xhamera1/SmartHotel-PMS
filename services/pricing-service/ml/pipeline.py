"""Random Forest pipeline and leakage-safe hyperparameter tuning."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ml.features import CATEGORICAL_FEATURES, FEATURE_NAMES, NUMERIC_FEATURES
from ml.splitting import (
    DEFAULT_HOLDOUT_MONTHS,
    ExpandingWindowSplit,
    TemporalSplit,
    temporal_train_test_split,
)

DEFAULT_RANDOM_STATE = 42
DEFAULT_CV_SPLITS = 5
DEFAULT_SEARCH_ITERATIONS = 30

RANDOM_FOREST_PARAM_DISTRIBUTIONS: dict[str, Sequence[object]] = {
    "regressor__n_estimators": tuple(range(200, 601)),
    "regressor__max_depth": tuple(range(8, 25)),
    "regressor__min_samples_leaf": tuple(range(1, 21)),
    "regressor__max_features": ("sqrt", "log2", 0.5, 0.75, 1.0),
}


@dataclass(frozen=True)
class TrainingConfig:
    """Reproducible knobs for temporal Random Forest tuning."""

    holdout_months: int = DEFAULT_HOLDOUT_MONTHS
    cv_splits: int = DEFAULT_CV_SPLITS
    cv_validation_days: int | None = None
    cv_gap_days: int = 0
    search_iterations: int = DEFAULT_SEARCH_ITERATIONS
    random_state: int = DEFAULT_RANDOM_STATE
    n_jobs: int = 1

    def __post_init__(self) -> None:
        if self.holdout_months < 1:
            raise ValueError("holdout_months must be >= 1")
        if self.cv_splits < 2:
            raise ValueError("cv_splits must be >= 2")
        if self.cv_validation_days is not None and self.cv_validation_days < 1:
            raise ValueError("cv_validation_days must be None or >= 1")
        if self.cv_gap_days < 0:
            raise ValueError("cv_gap_days must be >= 0")
        if self.search_iterations < 1:
            raise ValueError("search_iterations must be >= 1")
        if self.n_jobs == 0:
            raise ValueError("n_jobs must not be 0")


@dataclass(frozen=True)
class TrainingResult:
    """Fitted search plus the untouched holdout reserved for evaluation."""

    search: RandomizedSearchCV
    split: TemporalSplit
    config: TrainingConfig
    feature_names: tuple[str, ...]

    @property
    def best_pipeline(self) -> Pipeline:
        return self.search.best_estimator_


def build_random_forest_pipeline(
    *,
    random_state: int = DEFAULT_RANDOM_STATE,
    n_jobs: int = 1,
    feature_names: Sequence[str] = FEATURE_NAMES,
) -> Pipeline:
    """Build one-hot room type + passthrough numeric features + Random Forest."""

    regressor = RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=1,
        max_features=1.0,
        random_state=random_state,
        n_jobs=n_jobs,
    )
    return Pipeline(
        [
            ("preprocessor", build_feature_preprocessor(feature_names=feature_names)),
            ("regressor", regressor),
        ]
    )


def build_feature_preprocessor(
    *, feature_names: Sequence[str] = FEATURE_NAMES
) -> ColumnTransformer:
    """Build the shared one-hot/passthrough sklearn transformer."""

    selected = tuple(feature_names)
    if not selected:
        raise ValueError("feature_names must not be empty")
    if len(set(selected)) != len(selected):
        raise ValueError("feature_names must not contain duplicates")
    unknown = sorted(set(selected) - set(FEATURE_NAMES))
    if unknown:
        raise ValueError(f"unknown feature names: {unknown}")
    categorical = [name for name in CATEGORICAL_FEATURES if name in selected]
    numeric = [name for name in NUMERIC_FEATURES if name in selected]
    transformers: list[tuple[str, object, list[str]]] = []
    if categorical:
        transformers.append(
            (
                "room_type",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical,
            )
        )
    if numeric:
        transformers.append(("numeric", "passthrough", numeric))
    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        verbose_feature_names_out=False,
    )


def build_randomized_search(
    *,
    cv: ExpandingWindowSplit,
    n_iter: int = DEFAULT_SEARCH_ITERATIONS,
    random_state: int = DEFAULT_RANDOM_STATE,
    n_jobs: int = 1,
    param_distributions: Mapping[str, Sequence[object]] | None = None,
    feature_names: Sequence[str] = FEATURE_NAMES,
) -> RandomizedSearchCV:
    """Create deterministic RandomizedSearchCV scored by validation MAE."""

    if n_iter < 1:
        raise ValueError("n_iter must be >= 1")
    distributions = (
        RANDOM_FOREST_PARAM_DISTRIBUTIONS
        if param_distributions is None
        else dict(param_distributions)
    )
    return RandomizedSearchCV(
        estimator=build_random_forest_pipeline(
            random_state=random_state,
            n_jobs=n_jobs,
            feature_names=feature_names,
        ),
        param_distributions=distributions,
        n_iter=n_iter,
        scoring="neg_mean_absolute_error",
        n_jobs=n_jobs,
        cv=cv,
        refit=True,
        random_state=random_state,
        return_train_score=False,
        error_score="raise",
    )


def tune_random_forest(
    snapshots: pd.DataFrame,
    *,
    config: TrainingConfig | None = None,
    feature_names: Sequence[str] = FEATURE_NAMES,
    param_distributions: Mapping[str, Sequence[object]] | None = None,
) -> TrainingResult:
    """Tune only on historical rows and retain the final six-month holdout.

    Cross-validation scores are tuning diagnostics, not final reported metrics.
    The returned ``split.X_test`` / ``split.y_test`` are never passed to ``fit``;
    Step 4 evaluates the selected pipeline on them exactly once.
    """

    training_config = config or TrainingConfig()
    selected_features = tuple(feature_names)
    split = temporal_train_test_split(snapshots, holdout_months=training_config.holdout_months)
    cv = ExpandingWindowSplit(
        n_splits=training_config.cv_splits,
        validation_days=training_config.cv_validation_days,
        gap_days=training_config.cv_gap_days,
    )
    search = build_randomized_search(
        cv=cv,
        n_iter=training_config.search_iterations,
        random_state=training_config.random_state,
        n_jobs=training_config.n_jobs,
        feature_names=selected_features,
        param_distributions=param_distributions,
    )
    search.fit(split.X_train, split.y_train, groups=split.train_dates)
    return TrainingResult(
        search=search,
        split=split,
        config=training_config,
        feature_names=selected_features,
    )
