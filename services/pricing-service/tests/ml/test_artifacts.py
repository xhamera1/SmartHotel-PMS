"""Tests for versioned model artifacts and metadata provenance."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import joblib
import pandas as pd

from ml.artifacts import load_artifact_metadata, save_model_artifact, sha256_file
from ml.evaluation import EvaluationResult
from ml.features import (
    FEATURE_NAMES,
    FEATURE_SCHEMA_HASH,
    TARGET_NAME,
    build_feature_frame,
    build_feature_row,
)
from ml.pipeline import TrainingConfig, TrainingResult, build_random_forest_pipeline
from ml.splitting import TemporalSplit


class _FittedSearch:
    def __init__(self, pipeline) -> None:
        self.best_estimator_ = pipeline
        self.best_params_ = {"regressor__n_estimators": 5}


def _training_result(evaluation_split: TemporalSplit) -> TrainingResult:
    pipeline = build_random_forest_pipeline(random_state=42, n_jobs=1).set_params(
        regressor__n_estimators=5
    )
    pipeline.fit(evaluation_split.X_train, evaluation_split.y_train)
    return TrainingResult(
        search=_FittedSearch(pipeline),  # type: ignore[arg-type]
        split=evaluation_split,
        config=TrainingConfig(cv_splits=2, search_iterations=1),
        feature_names=FEATURE_NAMES,
    )


def _split() -> TemporalSplit:
    rows: list[dict[str, object]] = []
    targets: list[float] = []
    dates: list[pd.Timestamp] = []
    for offset in range(20):
        stay_date = date(2024, 1, 1) + timedelta(days=offset)
        rows.append(
            build_feature_row(
                stay_date=stay_date,
                lead_time_days=14,
                occupancy_rate=offset / 20,
                rooms_remaining=20 - offset,
                base_price=250.0,
                room_type="STD",
                demand_indicator=offset,
                event_count_active=0,
                max_event_score=0,
            )
        )
        targets.append(1.0 + offset / 100)
        dates.append(pd.Timestamp(stay_date))
    X = build_feature_frame(rows)
    y = pd.Series(targets, name=TARGET_NAME)
    date_series = pd.Series(dates, name="stay_date")
    return TemporalSplit(
        cutoff=date_series.iloc[14],
        test_start=date_series.iloc[15],
        X_train=X.iloc[:15].reset_index(drop=True),
        y_train=y.iloc[:15].reset_index(drop=True),
        train_dates=date_series.iloc[:15].reset_index(drop=True),
        X_test=X.iloc[15:].reset_index(drop=True),
        y_test=y.iloc[15:].reset_index(drop=True),
        test_dates=date_series.iloc[15:].reset_index(drop=True),
    )


def test_model_artifact_contains_model_and_complete_metadata(tmp_path) -> None:
    evaluation_split = _split()
    dataset = tmp_path / "snapshots.parquet"
    pd.concat([evaluation_split.X_train, evaluation_split.y_train], axis="columns").to_parquet(
        dataset
    )
    metrics = {"models": {"random_forest": {"overall": {"multiplier": {"mae": 0.1}}}}}
    evaluation = EvaluationResult(
        metrics=metrics,
        metrics_path=tmp_path / "metrics.json",
        figure_paths={},
    )

    artifact = save_model_artifact(
        _training_result(evaluation_split),
        evaluation,
        dataset_path=dataset,
        artifact_root=tmp_path / "models",
        version="rf-test-1",
        git_sha="a" * 40,
        trained_at=datetime(2026, 9, 17, 12, 0, tzinfo=UTC),
    )

    assert artifact.model_path.is_file()
    assert artifact.metadata_path.is_file()
    loaded_model = joblib.load(artifact.model_path)
    assert len(loaded_model.predict(evaluation_split.X_test.head(2))) == 2
    metadata = json.loads(artifact.metadata_path.read_text(encoding="utf-8"))
    assert metadata["dataset_hash"] == sha256_file(dataset)
    assert metadata["feature_schema_hash"] == FEATURE_SCHEMA_HASH
    assert metadata["git_sha"] == "a" * 40
    assert metadata["config"]["model_features"] == list(FEATURE_NAMES)
    assert metadata["metrics"] == metrics
    assert load_artifact_metadata(artifact.metadata_path) == metadata


def test_artifact_version_cannot_escape_model_root(tmp_path) -> None:
    evaluation_split = _split()
    dataset = tmp_path / "snapshots.parquet"
    pd.DataFrame({"value": [1]}).to_parquet(dataset)
    evaluation = EvaluationResult({}, Path("metrics.json"), {})

    try:
        save_model_artifact(
            _training_result(evaluation_split),
            evaluation,
            dataset_path=dataset,
            artifact_root=tmp_path / "models",
            version="../escape",
            git_sha="b" * 40,
        )
    except ValueError as exc:
        assert "version" in str(exc)
    else:
        raise AssertionError("unsafe artifact version was accepted")
