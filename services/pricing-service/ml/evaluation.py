"""Offline holdout evaluation, baseline comparison, and figure generation."""

from __future__ import annotations

import json
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
    root_mean_squared_error,
)

from ml.baselines import (
    BASELINE_LINEAR,
    BASELINE_RULE_BASED,
    BASELINE_STATIC,
    MONTH_MULTIPLIERS,
    RANDOM_FOREST_MODEL,
    WEEKDAY_MULTIPLIERS,
    fit_baselines,
)
from ml.features import FEATURE_NAMES, FEATURE_SCHEMA_HASH
from ml.pipeline import TrainingResult
from ml.splitting import TemporalSplit

METRICS_FILENAME = "metrics.json"
PREDICTED_VS_ACTUAL_FILENAME = "predicted_vs_actual.png"
RESIDUAL_DISTRIBUTION_FILENAME = "residual_distribution.png"
PERMUTATION_IMPORTANCE_FILENAME = "permutation_feature_importance.png"
LEARNING_CURVE_FILENAME = "learning_curve.png"
BATCH_PREDICT_ROWS = 366
BATCH_PREDICT_BUDGET_MS = 150.0


class Regressor(Protocol):
    def predict(self, X: pd.DataFrame) -> object: ...


@dataclass(frozen=True)
class EvaluationResult:
    metrics: dict[str, object]
    metrics_path: Path
    figure_paths: dict[str, Path]


def regression_metrics(
    actual_multiplier: object,
    predicted_multiplier: object,
    base_price: object,
) -> dict[str, dict[str, float | None]]:
    """Calculate MAE/RMSE/R²/MAPE for multiplier and resulting PLN price.

    MAPE is reported as a percentage rather than sklearn's fractional value.
    """

    actual = _finite_vector(actual_multiplier, "actual_multiplier")
    predicted = _finite_vector(predicted_multiplier, "predicted_multiplier")
    prices = _finite_vector(base_price, "base_price")
    if len(actual) != len(predicted) or len(actual) != len(prices):
        raise ValueError("actual, predicted, and base_price must have equal lengths")
    if len(actual) == 0:
        raise ValueError("metrics require at least one row")
    if (actual <= 0).any() or (prices <= 0).any():
        raise ValueError("actual_multiplier and base_price must be positive")

    return {
        "multiplier": _metric_set(actual, predicted),
        "price_pln": _metric_set(actual * prices, predicted * prices),
    }


def _finite_vector(values: object, name: str) -> np.ndarray:
    try:
        vector = np.asarray(values, dtype="float64").reshape(-1)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not np.isfinite(vector).all():
        raise ValueError(f"{name} must contain only finite values")
    return vector


def _metric_set(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float | None]:
    r2 = float(r2_score(actual, predicted)) if len(actual) >= 2 else None
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(root_mean_squared_error(actual, predicted)),
        "r2": r2,
        "mape": float(mean_absolute_percentage_error(actual, predicted) * 100.0),
    }


def evaluate_holdout(
    *,
    random_forest: Regressor,
    split: TemporalSplit,
    output_dir: Path,
    permutation_repeats: int = 10,
    random_state: int = 42,
    n_jobs: int = 1,
    feature_names: tuple[str, ...] = FEATURE_NAMES,
) -> EvaluationResult:
    """Evaluate frozen RF and baselines on the same untouched test partition."""

    if permutation_repeats < 1:
        raise ValueError("permutation_repeats must be >= 1")
    output_dir.mkdir(parents=True, exist_ok=True)

    baselines = fit_baselines(
        split.X_train,
        split.y_train,
        n_jobs=n_jobs,
        feature_names=feature_names,
    )
    models: dict[str, Regressor] = {
        RANDOM_FOREST_MODEL: random_forest,
        **baselines,  # type: ignore[dict-item]
    }
    predictions = {
        name: _validated_predictions(model.predict(split.X_test), len(split.X_test), name)
        for name, model in models.items()
    }
    actual = split.y_test.to_numpy(dtype="float64")
    base_price = split.X_test["base_price"].to_numpy(dtype="float64")

    model_metrics: dict[str, object] = {}
    for name, predicted in predictions.items():
        model_metrics[name] = {
            "overall": regression_metrics(actual, predicted, base_price),
            "segments": _segment_breakdowns(split, actual, predicted, base_price),
        }

    importance = _permutation_importance(
        random_forest,
        split,
        repeats=permutation_repeats,
        random_state=random_state,
        n_jobs=n_jobs,
        feature_names=feature_names,
    )
    comparison = _comparison(model_metrics)
    latency = measure_batch_predict_ms(
        random_forest,
        split.X_test,
        n_rows=BATCH_PREDICT_ROWS,
    )
    figure_paths = {
        "predicted_vs_actual": output_dir / PREDICTED_VS_ACTUAL_FILENAME,
        "residual_distribution": output_dir / RESIDUAL_DISTRIBUTION_FILENAME,
        "permutation_feature_importance": output_dir / PERMUTATION_IMPORTANCE_FILENAME,
    }
    _plot_predicted_vs_actual(
        actual,
        predictions[RANDOM_FOREST_MODEL],
        base_price,
        figure_paths["predicted_vs_actual"],
    )
    _plot_residual_distribution(actual, predictions, figure_paths["residual_distribution"])
    _plot_permutation_importance(importance, figure_paths["permutation_feature_importance"])

    metrics: dict[str, object] = {
        "feature_schema_hash": FEATURE_SCHEMA_HASH,
        "model_features": list(feature_names),
        "test_window": {
            "cutoff": split.cutoff.date().isoformat(),
            "start": split.test_start.date().isoformat(),
            "end": pd.Timestamp(split.test_dates.max()).date().isoformat(),
            "rows": len(split.X_test),
        },
        "metric_definitions": {
            "mape": "percentage (0 means perfect; 10 means 10%)",
            "price_pln": "base_price * price_multiplier",
        },
        "baseline_definitions": {
            BASELINE_STATIC: "constant price_multiplier = 1.0",
            BASELINE_RULE_BASED: {
                "formula": "weekday_multiplier[day_of_week] * month_multiplier[month]",
                "weekday_multipliers_monday_to_sunday": list(WEEKDAY_MULTIPLIERS),
                "month_multipliers_january_to_december": list(MONTH_MULTIPLIERS),
            },
            BASELINE_LINEAR: "LinearRegression on the shared transformed feature set",
        },
        "permutation_importance_config": {
            "scoring": "neg_mean_absolute_error",
            "repeats": permutation_repeats,
            "random_state": random_state,
        },
        "latency": latency,
        "models": model_metrics,
        "comparison": comparison,
        "permutation_importance": importance,
        "figures": {name: path.name for name, path in figure_paths.items()},
    }
    metrics_path = output_dir / METRICS_FILENAME
    metrics_path.write_text(
        json.dumps(metrics, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return EvaluationResult(metrics=metrics, metrics_path=metrics_path, figure_paths=figure_paths)


def evaluate_training_result(
    training: TrainingResult,
    *,
    output_dir: Path,
    permutation_repeats: int = 10,
    random_state: int = 42,
    n_jobs: int = 1,
    learning_curve_points: int = 5,
) -> EvaluationResult:
    """Evaluate the selected RF from Step 2 without retraining on test data."""

    result = evaluate_holdout(
        random_forest=training.best_pipeline,
        split=training.split,
        output_dir=output_dir,
        permutation_repeats=permutation_repeats,
        random_state=random_state,
        n_jobs=n_jobs,
        feature_names=training.feature_names,
    )
    curve = compute_learning_curve(training, n_points=learning_curve_points)
    curve_path = output_dir / LEARNING_CURVE_FILENAME
    plot_learning_curve(curve, curve_path)
    metrics = dict(result.metrics)
    figures = dict(metrics.get("figures", {}))  # type: ignore[arg-type]
    figures["learning_curve"] = curve_path.name
    metrics["learning_curve"] = curve
    metrics["figures"] = figures
    figure_paths = dict(result.figure_paths)
    figure_paths["learning_curve"] = curve_path
    metrics_path = result.metrics_path
    metrics_path.write_text(
        json.dumps(metrics, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return EvaluationResult(metrics=metrics, metrics_path=metrics_path, figure_paths=figure_paths)


def measure_batch_predict_ms(
    model: Regressor,
    features: pd.DataFrame,
    *,
    n_rows: int = BATCH_PREDICT_ROWS,
    budget_ms: float = BATCH_PREDICT_BUDGET_MS,
    repeats: int = 3,
) -> dict[str, float | int | bool]:
    """Time a fixed-size batch predict; budget is ≪ 150 ms for 366 rows."""

    if n_rows < 1:
        raise ValueError("n_rows must be >= 1")
    if repeats < 1:
        raise ValueError("repeats must be >= 1")
    if features.empty:
        raise ValueError("features must not be empty")
    sample = features
    if len(sample) < n_rows:
        reps = int(np.ceil(n_rows / len(sample)))
        sample = pd.concat([sample] * reps, ignore_index=True)
    batch = sample.iloc[:n_rows].reset_index(drop=True)
    # Warm-up so first-call overhead does not dominate CI noise.
    model.predict(batch)
    times_ms: list[float] = []
    for _ in range(repeats):
        started = time.perf_counter()
        model.predict(batch)
        times_ms.append((time.perf_counter() - started) * 1000.0)
    median_ms = float(np.median(times_ms))
    return {
        "batch_rows": n_rows,
        "repeats": repeats,
        "median_ms": median_ms,
        "budget_ms": budget_ms,
        "passed": median_ms < budget_ms,
    }


def compute_learning_curve(
    training: TrainingResult,
    *,
    n_points: int = 5,
) -> list[dict[str, float | int]]:
    """Validation MAE vs expanding train-date count on the historical partition."""

    if n_points < 2:
        raise ValueError("n_points must be >= 2")
    X = training.split.X_train
    y = training.split.y_train
    dates = training.split.train_dates
    unique_dates = sorted(pd.Timestamp(d) for d in dates.unique())
    if len(unique_dates) < 4:
        return []

    val_count = max(7, len(unique_dates) // 5)
    val_dates = set(unique_dates[-val_count:])
    train_pool = [d for d in unique_dates if d not in val_dates]
    if not train_pool:
        return []

    date_values = pd.to_datetime(dates).dt.normalize()
    val_mask = date_values.isin(val_dates)
    X_val = X.loc[val_mask]
    y_val = y.loc[val_mask]
    if X_val.empty:
        return []

    points: list[dict[str, float | int]] = []
    for index in range(1, n_points + 1):
        n_dates = max(1, int(round(len(train_pool) * index / n_points)))
        selected = set(train_pool[:n_dates])
        train_mask = date_values.isin(selected)
        if int(train_mask.sum()) < 2:
            continue
        model = clone(training.best_pipeline)
        model.fit(X.loc[train_mask], y.loc[train_mask])
        predicted = np.asarray(model.predict(X_val), dtype="float64")
        points.append(
            {
                "train_dates": n_dates,
                "train_rows": int(train_mask.sum()),
                "val_mae": float(mean_absolute_error(y_val, predicted)),
            }
        )
    return points


def plot_learning_curve(points: Sequence[Mapping[str, float | int]], path: Path) -> Path:
    """Persist train-size vs validation MAE figure for the thesis."""

    plt = _plotting()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if points:
        xs = [int(p["train_dates"]) for p in points]
        ys = [float(p["val_mae"]) for p in points]
        ax.plot(xs, ys, marker="o", color="#1d3557")
    ax.set_xlabel("Training stay-date count")
    ax.set_ylabel("Validation MAE (multiplier)")
    ax.set_title("Learning curve (expanding train window)")
    path.parent.mkdir(parents=True, exist_ok=True)
    _save_figure(fig, path, plt)
    return path


def _validated_predictions(values: object, expected_rows: int, model_name: str) -> np.ndarray:
    predicted = _finite_vector(values, f"{model_name} predictions")
    if len(predicted) != expected_rows:
        raise ValueError(
            f"{model_name} returned {len(predicted)} predictions for {expected_rows} rows"
        )
    return predicted


def _segment_breakdowns(
    split: TemporalSplit,
    actual: np.ndarray,
    predicted: np.ndarray,
    base_price: np.ndarray,
) -> dict[str, dict[str, dict[str, dict[str, float | None]]]]:
    segment_values: dict[str, pd.Series] = {
        "month": split.X_test["month"].astype("int64").astype("string"),
        "event_night": pd.Series(
            np.where(split.X_test["event_count_active"].to_numpy() > 0, "event", "normal")
        ),
        "room_type": split.X_test["room_type"].astype("string"),
    }
    breakdowns: dict[str, dict[str, dict[str, dict[str, float | None]]]] = {}
    for segment_name, labels in segment_values.items():
        groups: dict[str, dict[str, dict[str, float | None]]] = {}
        for label in sorted(labels.dropna().unique(), key=str):
            mask = labels.eq(label).to_numpy(dtype="bool")
            groups[str(label)] = regression_metrics(actual[mask], predicted[mask], base_price[mask])
        breakdowns[segment_name] = groups
    return breakdowns


def _permutation_importance(
    model: Regressor,
    split: TemporalSplit,
    *,
    repeats: int,
    random_state: int,
    n_jobs: int,
    feature_names: tuple[str, ...],
) -> list[dict[str, float | str]]:
    result = permutation_importance(
        model,
        split.X_test.loc[:, list(feature_names)],
        split.y_test,
        scoring="neg_mean_absolute_error",
        n_repeats=repeats,
        random_state=random_state,
        n_jobs=n_jobs,
    )
    rows = [
        {
            "feature": feature,
            "importance_mean": float(mean),
            "importance_std": float(std),
        }
        for feature, mean, std in zip(
            feature_names,
            result.importances_mean,
            result.importances_std,
            strict=True,
        )
    ]
    return sorted(rows, key=lambda row: float(row["importance_mean"]), reverse=True)


def _comparison(model_metrics: Mapping[str, object]) -> dict[str, object]:
    rf = _overall_metrics(model_metrics[RANDOM_FOREST_MODEL])
    baseline_comparison: dict[str, dict[str, float | bool]] = {}
    wins: list[bool] = []
    for name, raw_metrics in model_metrics.items():
        if name == RANDOM_FOREST_MODEL:
            continue
        baseline = _overall_metrics(raw_metrics)
        multiplier_delta = baseline["multiplier"]["mae"] - rf["multiplier"]["mae"]
        price_delta = baseline["price_pln"]["mae"] - rf["price_pln"]["mae"]
        beats = multiplier_delta > 0 and price_delta > 0
        wins.append(beats)
        baseline_comparison[name] = {
            "rf_beats_baseline": beats,
            "multiplier_mae_improvement": multiplier_delta,
            "price_pln_mae_improvement": price_delta,
        }
    return {
        "criterion": "RF MAE must be lower for both multiplier and PLN price",
        "rf_beats_all_baselines": all(wins),
        "baselines": baseline_comparison,
    }


def _overall_metrics(raw: object) -> dict[str, dict[str, float]]:
    model = raw  # keep the narrowing/check in one place for JSON-like structures
    if not isinstance(model, dict) or not isinstance(model.get("overall"), dict):
        raise TypeError("model metrics missing overall section")
    return model["overall"]  # type: ignore[return-value]


def _plotting():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _plot_predicted_vs_actual(
    actual: np.ndarray,
    predicted: np.ndarray,
    base_price: np.ndarray,
    path: Path,
) -> None:
    plt = _plotting()
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    pairs = (
        (actual, predicted, "Price multiplier"),
        (actual * base_price, predicted * base_price, "Resulting price (PLN)"),
    )
    for ax, (actual_values, predicted_values, label) in zip(axes, pairs, strict=True):
        low = float(min(actual_values.min(), predicted_values.min()))
        high = float(max(actual_values.max(), predicted_values.max()))
        ax.scatter(actual_values, predicted_values, alpha=0.25, s=12, edgecolors="none")
        ax.plot([low, high], [low, high], linestyle="--", color="#bc4749")
        ax.set_xlabel(f"Actual {label.lower()}")
        ax.set_ylabel(f"Predicted {label.lower()}")
        ax.set_title(label)
    fig.suptitle("Random Forest: predicted vs actual")
    _save_figure(fig, path, plt)


def _plot_residual_distribution(
    actual: np.ndarray,
    predictions: Mapping[str, np.ndarray],
    path: Path,
) -> None:
    plt = _plotting()
    fig, ax = plt.subplots(figsize=(9, 5))
    for name, predicted in predictions.items():
        ax.hist(actual - predicted, bins=40, alpha=0.35, density=True, label=name)
    ax.axvline(0.0, linestyle="--", color="black", linewidth=1)
    ax.set_xlabel("Residual (actual multiplier - predicted multiplier)")
    ax.set_ylabel("Density")
    ax.set_title("Holdout residual distributions")
    ax.legend()
    _save_figure(fig, path, plt)


def _plot_permutation_importance(
    importance: list[dict[str, float | str]],
    path: Path,
) -> None:
    plt = _plotting()
    ordered = list(reversed(importance))
    labels = [str(row["feature"]) for row in ordered]
    means = [float(row["importance_mean"]) for row in ordered]
    errors = [float(row["importance_std"]) for row in ordered]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(labels, means, xerr=errors, color="#457b9d", alpha=0.85)
    ax.axvline(0.0, color="black", linewidth=0.8)
    ax.set_xlabel("Decrease in holdout score (negative MAE)")
    ax.set_title("Random Forest permutation feature importance")
    _save_figure(fig, path, plt)


def _save_figure(fig: object, path: Path, plt: object) -> None:
    fig.tight_layout()  # type: ignore[attr-defined]
    fig.savefig(path, dpi=140, bbox_inches="tight")  # type: ignore[attr-defined]
    plt.close(fig)  # type: ignore[attr-defined]
