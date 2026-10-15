"""Immutable in-memory model holder and registry/joblib loading."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any

import joblib
import sqlalchemy as sa
from sklearn.pipeline import Pipeline

from ml.features import FEATURE_SCHEMA_HASH

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelState:
    version: str
    pipeline: Pipeline
    feature_schema_hash: str
    metrics: dict[str, Any]
    trained_at: str
    artifact_path: str
    top_signals: tuple[str, ...]


class ModelHolder:
    """Thread-safe atomic swap of the active serving model."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._state: ModelState | None = None

    @property
    def state(self) -> ModelState | None:
        with self._lock:
            return self._state

    def set(self, state: ModelState | None) -> None:
        with self._lock:
            self._state = state

    @property
    def is_loaded(self) -> bool:
        return self.state is not None


def _top_signals_from_metrics(metrics: dict[str, Any]) -> tuple[str, ...]:
    importance = metrics.get("permutation_importance")
    if isinstance(importance, list) and importance:
        names = [
            str(row["feature"])
            for row in importance[:3]
            if isinstance(row, dict) and "feature" in row
        ]
        if names:
            return tuple(names)
    return ("demand_indicator", "occupancy_rate", "is_weekend")


def load_pipeline_from_artifact(artifact_path: Path) -> Pipeline:
    pipeline = joblib.load(artifact_path)
    if not hasattr(pipeline, "predict"):
        raise TypeError(f"artifact is not a predictor: {artifact_path}")
    return pipeline


def load_active_model(
    engine: sa.Engine,
    *,
    fixture_dir: Path | None = None,
    allow_fixture: bool = True,
) -> ModelState | None:
    """Load active registry model, or fall back to committed fixture for local/demo."""

    row = None
    try:
        with engine.connect() as connection:
            row = (
                connection.execute(
                    sa.text(
                        """
                    SELECT version, feature_schema_hash, artifact_path, metrics, trained_at
                    FROM pricing.model_registry
                    WHERE is_active = true
                    LIMIT 1
                    """
                    )
                )
                .mappings()
                .first()
            )
    except Exception:
        logger.exception("failed to read active model from registry")
        if allow_fixture and fixture_dir is not None:
            return load_fixture_model(fixture_dir)
        return None

    if row is not None:
        schema_hash = str(row["feature_schema_hash"])
        if schema_hash != FEATURE_SCHEMA_HASH:
            logger.error(
                "active model schema hash mismatch: registry=%s expected=%s",
                schema_hash,
                FEATURE_SCHEMA_HASH,
            )
            return None
        artifact = Path(str(row["artifact_path"]))
        if not artifact.is_file():
            logger.error("active model artifact missing: %s", artifact)
            return None
        metrics = row["metrics"] if isinstance(row["metrics"], dict) else {}
        pipeline = load_pipeline_from_artifact(artifact)
        return ModelState(
            version=str(row["version"]),
            pipeline=pipeline,
            feature_schema_hash=schema_hash,
            metrics=metrics,
            trained_at=row["trained_at"].isoformat()
            if hasattr(row["trained_at"], "isoformat")
            else str(row["trained_at"]),
            artifact_path=str(artifact),
            top_signals=_top_signals_from_metrics(metrics),
        )

    if allow_fixture and fixture_dir is not None:
        return load_fixture_model(fixture_dir)
    return None


def load_fixture_model(fixture_dir: Path) -> ModelState | None:
    model_path = fixture_dir / "model.joblib"
    meta_path = fixture_dir / "metadata.json"
    if not model_path.is_file() or not meta_path.is_file():
        logger.warning("fixture model not found under %s", fixture_dir)
        return None
    import json

    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    schema_hash = str(metadata.get("feature_schema_hash", ""))
    if schema_hash != FEATURE_SCHEMA_HASH:
        logger.error("fixture schema hash mismatch: %s", schema_hash)
        return None
    metrics = metadata.get("metrics") if isinstance(metadata.get("metrics"), dict) else {}
    pipeline = load_pipeline_from_artifact(model_path)
    return ModelState(
        version=str(metadata.get("version", "fixture-tiny")),
        pipeline=pipeline,
        feature_schema_hash=schema_hash,
        metrics=metrics,
        trained_at=str(metadata.get("trained_at", "")),
        artifact_path=str(model_path),
        top_signals=_top_signals_from_metrics(metrics),
    )
