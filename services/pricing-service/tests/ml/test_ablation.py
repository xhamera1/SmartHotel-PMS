"""Tests for the reproducible RQ2 event-feature ablation."""

from __future__ import annotations

import json
from datetime import date, timedelta

import pandas as pd
import pytest

from ml.ablation import (
    WITH_EVENTS,
    WITHOUT_EVENTS,
    build_ablation_comparison,
    run_event_ablation,
)
from ml.features import EVENT_FEATURES, FEATURE_NAMES, TARGET_NAME, build_feature_row
from ml.pipeline import TrainingConfig


def _snapshots(days: int = 260) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    start = date(2024, 1, 1)
    for offset in range(days):
        stay_date = start + timedelta(days=offset)
        event = offset % 9 == 0
        demand = 80 if event else 0
        features = build_feature_row(
            stay_date=stay_date,
            lead_time_days=14,
            occupancy_rate=(offset % 10) / 10,
            rooms_remaining=10 - offset % 10,
            base_price=250.0,
            room_type="STD",
            demand_indicator=demand,
            event_count_active=int(event),
            max_event_score=demand,
        )
        rows.append(
            {
                "stay_date": stay_date,
                **features,
                TARGET_NAME: 0.9 + 0.004 * demand + 0.1 * float(features["is_weekend"]),
            }
        )
    return pd.DataFrame(rows)


def _metrics(mae: float, r2: float) -> dict[str, object]:
    metric_set = {"mae": mae, "rmse": mae * 1.2, "r2": r2, "mape": mae * 10}
    return {
        "models": {
            "random_forest": {"overall": {"multiplier": metric_set, "price_pln": metric_set}}
        }
    }


def test_comparison_uses_positive_gain_when_event_features_help() -> None:
    result = build_ablation_comparison(_metrics(0.1, 0.9), _metrics(0.2, 0.7))

    rows = result["rows"]
    assert isinstance(rows, list)
    mae = next(row for row in rows if row["target"] == "multiplier" and row["metric"] == "mae")
    r2 = next(row for row in rows if row["target"] == "multiplier" and row["metric"] == "r2")
    assert mae["event_feature_gain"] == 0.1
    assert r2["event_feature_gain"] == pytest.approx(0.2)
    assert mae["event_features_improve"] is True
    assert result["dropped_features"] == list(EVENT_FEATURES)


def test_ablation_writes_both_metrics_and_generated_tables(tmp_path) -> None:
    params = {
        "regressor__n_estimators": [5],
        "regressor__max_depth": [8],
        "regressor__min_samples_leaf": [1],
        "regressor__max_features": [1.0],
    }
    result = run_event_ablation(
        _snapshots(),
        output_dir=tmp_path,
        config=TrainingConfig(
            holdout_months=2,
            cv_splits=2,
            cv_validation_days=20,
            search_iterations=1,
            n_jobs=1,
        ),
        permutation_repeats=1,
        param_distributions=params,
    )

    with_metrics = json.loads(
        result.evaluations[WITH_EVENTS].metrics_path.read_text(encoding="utf-8")
    )
    without_metrics = json.loads(
        result.evaluations[WITHOUT_EVENTS].metrics_path.read_text(encoding="utf-8")
    )
    assert with_metrics["model_features"] == list(FEATURE_NAMES)
    assert without_metrics["model_features"] == [
        feature for feature in FEATURE_NAMES if feature not in EVENT_FEATURES
    ]
    assert not set(EVENT_FEATURES) & {
        row["feature"] for row in without_metrics["permutation_importance"]
    }
    assert set(result.comparison_paths) == {"json", "csv", "markdown"}
    assert all(
        path.is_file() and path.stat().st_size > 0 for path in result.comparison_paths.values()
    )
