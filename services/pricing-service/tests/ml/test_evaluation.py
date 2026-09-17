"""Tests for honest holdout metrics, segments, figures, and JSON artifacts."""

from __future__ import annotations

import json
from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from ml.baselines import (
    BASELINE_LINEAR,
    BASELINE_RULE_BASED,
    BASELINE_STATIC,
    RANDOM_FOREST_MODEL,
)
from ml.evaluation import evaluate_holdout, regression_metrics
from ml.features import (
    FEATURE_NAMES,
    FEATURE_SCHEMA_HASH,
    TARGET_NAME,
    build_feature_frame,
    build_feature_row,
)
from ml.pipeline import build_random_forest_pipeline
from ml.splitting import TemporalSplit


def evaluation_split() -> TemporalSplit:
    rows: list[dict[str, object]] = []
    targets: list[float] = []
    dates: list[pd.Timestamp] = []
    start = date(2024, 1, 1)
    for offset in range(80):
        stay_date = start + timedelta(days=offset)
        for room_type, base_price in (("STD", 250.0), ("DLX", 420.0)):
            event_count = 1 if offset % 7 == 0 else 0
            demand = 70 if event_count else offset % 30
            row = build_feature_row(
                stay_date=stay_date,
                lead_time_days=14,
                occupancy_rate=(offset % 10) / 10,
                rooms_remaining=10 - offset % 10,
                base_price=base_price,
                room_type=room_type,
                demand_indicator=demand,
                event_count_active=event_count,
                max_event_score=demand,
            )
            rows.append(row)
            targets.append(
                0.9
                + 0.004 * demand
                + 0.15 * float(row["is_weekend"])
                + (0.08 if room_type == "DLX" else 0.0)
            )
            dates.append(pd.Timestamp(stay_date))

    X = build_feature_frame(rows)
    y = pd.Series(targets, name=TARGET_NAME, dtype="float64")
    date_series = pd.Series(dates, name="stay_date")
    train_rows = 60 * 2
    return TemporalSplit(
        cutoff=date_series.iloc[train_rows - 1],
        test_start=date_series.iloc[train_rows],
        X_train=X.iloc[:train_rows].reset_index(drop=True),
        y_train=y.iloc[:train_rows].reset_index(drop=True),
        train_dates=date_series.iloc[:train_rows].reset_index(drop=True),
        X_test=X.iloc[train_rows:].reset_index(drop=True),
        y_test=y.iloc[train_rows:].reset_index(drop=True),
        test_dates=date_series.iloc[train_rows:].reset_index(drop=True),
    )


def test_regression_metrics_cover_multiplier_and_pln() -> None:
    metrics = regression_metrics(
        actual_multiplier=[1.0, 2.0],
        predicted_multiplier=[1.1, 1.8],
        base_price=[100.0, 200.0],
    )

    assert metrics["multiplier"] == pytest.approx(
        {"mae": 0.15, "rmse": np.sqrt(0.025), "r2": 0.9, "mape": 10.0}
    )
    assert metrics["price_pln"] == pytest.approx(
        {"mae": 25.0, "rmse": np.sqrt(850.0), "r2": 0.9622222222, "mape": 10.0}
    )


def test_regression_metrics_use_json_safe_r2_for_single_row() -> None:
    metrics = regression_metrics([1.0], [1.1], [250.0])
    assert metrics["multiplier"]["r2"] is None
    assert metrics["price_pln"]["r2"] is None


@pytest.mark.parametrize(
    ("actual", "predicted", "base_price", "message"),
    [
        ([1.0], [1.0, 1.1], [250.0], "equal lengths"),
        ([0.0], [1.0], [250.0], "positive"),
        ([1.0], [np.inf], [250.0], "finite"),
    ],
)
def test_regression_metrics_reject_invalid_values(
    actual: list[float],
    predicted: list[float],
    base_price: list[float],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        regression_metrics(actual, predicted, base_price)


def test_evaluation_writes_complete_json_and_png_artifacts(tmp_path) -> None:
    split = evaluation_split()
    random_forest = build_random_forest_pipeline(random_state=42, n_jobs=1).set_params(
        regressor__n_estimators=20,
        regressor__max_depth=8,
    )
    random_forest.fit(split.X_train, split.y_train)

    result = evaluate_holdout(
        random_forest=random_forest,
        split=split,
        output_dir=tmp_path,
        permutation_repeats=2,
        random_state=42,
        n_jobs=1,
    )

    assert result.metrics_path == tmp_path / "metrics.json"
    persisted = json.loads(result.metrics_path.read_text(encoding="utf-8"))
    assert persisted == result.metrics
    assert persisted["feature_schema_hash"] == FEATURE_SCHEMA_HASH
    assert persisted["test_window"]["rows"] == len(split.X_test)
    assert set(persisted["models"]) == {
        RANDOM_FOREST_MODEL,
        BASELINE_STATIC,
        BASELINE_RULE_BASED,
        BASELINE_LINEAR,
    }
    for model_metrics in persisted["models"].values():
        assert set(model_metrics["overall"]) == {"multiplier", "price_pln"}
        assert set(model_metrics["overall"]["multiplier"]) == {"mae", "rmse", "r2", "mape"}
        assert set(model_metrics["segments"]) == {"month", "event_night", "room_type"}
    assert set(persisted["models"][RANDOM_FOREST_MODEL]["segments"]["event_night"]) == {
        "event",
        "normal",
    }
    assert isinstance(persisted["comparison"]["rf_beats_all_baselines"], bool)
    assert set(persisted["comparison"]["baselines"]) == {
        BASELINE_STATIC,
        BASELINE_RULE_BASED,
        BASELINE_LINEAR,
    }
    assert {row["feature"] for row in persisted["permutation_importance"]} == set(FEATURE_NAMES)
    for path in result.figure_paths.values():
        assert path.is_file()
        assert path.stat().st_size > 0
