"""Deterministic quick-training metric regression gate for CI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ml.artifacts import sha256_file
from ml.evaluation import regression_metrics
from ml.features import FEATURE_SCHEMA_HASH
from ml.pipeline import TrainingConfig, tune_random_forest

DEFAULT_TOLERANCE = 0.10
QUICK_METRICS_FILENAME = "quick_metrics.json"
GATE_REPORT_FILENAME = "gate_report.json"
PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[2]
DEFAULT_BASELINE = PACKAGE_ROOT / "baseline_metrics.json"
DEFAULT_DATASET = REPO_ROOT / "artifacts" / "datasets" / "default" / "snapshots.parquet"
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "ml-gate"

QUICK_TRAINING_CONFIG = TrainingConfig(
    holdout_months=6,
    cv_splits=3,
    cv_validation_days=60,
    search_iterations=1,
    random_state=42,
    n_jobs=1,
)
QUICK_PARAM_DISTRIBUTIONS: dict[str, list[object]] = {
    "regressor__n_estimators": [50],
    "regressor__max_depth": [12],
    "regressor__min_samples_leaf": [2],
    "regressor__max_features": [1.0],
}


class MetricRegressionError(RuntimeError):
    """Fresh metrics exceeded the accepted relative regression."""


def quick_train_metrics(dataset_path: Path) -> dict[str, object]:
    """Train the fixed low-cost CI model and return its two primary MAEs."""

    snapshots = pd.read_parquet(dataset_path)
    training = tune_random_forest(
        snapshots,
        config=QUICK_TRAINING_CONFIG,
        param_distributions=QUICK_PARAM_DISTRIBUTIONS,
    )
    predictions = training.best_pipeline.predict(training.split.X_test)
    metrics = regression_metrics(
        training.split.y_test,
        predictions,
        training.split.X_test["base_price"],
    )
    return {
        "protocol_version": 1,
        "feature_schema_hash": FEATURE_SCHEMA_HASH,
        "dataset_hash": sha256_file(dataset_path),
        "protocol": {
            "training_config": {
                "holdout_months": QUICK_TRAINING_CONFIG.holdout_months,
                "cv_splits": QUICK_TRAINING_CONFIG.cv_splits,
                "cv_validation_days": QUICK_TRAINING_CONFIG.cv_validation_days,
                "search_iterations": QUICK_TRAINING_CONFIG.search_iterations,
                "random_state": QUICK_TRAINING_CONFIG.random_state,
                "n_jobs": QUICK_TRAINING_CONFIG.n_jobs,
            },
            "fixed_params": {name: values[0] for name, values in QUICK_PARAM_DISTRIBUTIONS.items()},
        },
        "metrics": {
            "multiplier_mae": metrics["multiplier"]["mae"],
            "price_pln_mae": metrics["price_pln"]["mae"],
        },
    }


def compare_to_baseline(
    fresh: dict[str, object],
    baseline: dict[str, object],
    *,
    tolerance: float = DEFAULT_TOLERANCE,
) -> dict[str, object]:
    """Compare primary MAEs; equality at the 10% boundary passes."""

    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    if fresh.get("feature_schema_hash") != baseline.get("feature_schema_hash"):
        raise ValueError("fresh and baseline feature_schema_hash values differ")
    if fresh.get("protocol_version") != baseline.get("protocol_version"):
        raise ValueError("fresh and baseline protocol_version values differ")
    if fresh.get("protocol") != baseline.get("protocol"):
        raise ValueError("fresh and baseline quick-training protocols differ")
    fresh_metrics = _metric_values(fresh, "fresh")
    baseline_metrics = _metric_values(baseline, "baseline")
    comparisons: dict[str, dict[str, float | bool]] = {}
    passed = True
    for name in ("multiplier_mae", "price_pln_mae"):
        current = fresh_metrics[name]
        reference = baseline_metrics[name]
        if reference <= 0:
            raise ValueError(f"baseline {name} must be positive")
        limit = reference * (1.0 + tolerance)
        metric_passed = current <= limit
        passed = passed and metric_passed
        comparisons[name] = {
            "baseline": reference,
            "fresh": current,
            "maximum_allowed": limit,
            "relative_change": (current - reference) / reference,
            "passed": metric_passed,
        }
    return {
        "passed": passed,
        "tolerance": tolerance,
        "comparisons": comparisons,
    }


def run_gate(
    *,
    dataset_path: Path,
    baseline_path: Path = DEFAULT_BASELINE,
    output_dir: Path = DEFAULT_OUTPUT,
    tolerance: float = DEFAULT_TOLERANCE,
) -> dict[str, object]:
    """Run fresh training, persist evidence, and fail on excessive regression."""

    baseline = _read_json_object(baseline_path)
    fresh = quick_train_metrics(dataset_path)
    report = compare_to_baseline(fresh, baseline, tolerance=tolerance)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / QUICK_METRICS_FILENAME, fresh)
    _write_json(output_dir / GATE_REPORT_FILENAME, report)
    if not report["passed"]:
        raise MetricRegressionError(
            f"ML metric regression exceeds {tolerance:.0%}; see {output_dir / GATE_REPORT_FILENAME}"
        )
    return report


def _metric_values(payload: dict[str, object], label: str) -> dict[str, float]:
    metrics = payload.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError(f"{label} payload missing metrics")
    result: dict[str, float] = {}
    for name in ("multiplier_mae", "price_pln_mae"):
        value = metrics.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{label} metric {name} must be numeric")
        result[name] = float(value)
    return result


def _read_json_object(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the quick-training ML metric gate")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = run_gate(
            dataset_path=args.dataset,
            baseline_path=args.baseline,
            output_dir=args.output,
            tolerance=args.tolerance,
        )
    except (OSError, ValueError, MetricRegressionError) as exc:
        print(f"metric_gate_failed={exc}")
        return 1
    print(f"metric_gate_passed={report['passed']}")
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised as a CLI
    raise SystemExit(main())
