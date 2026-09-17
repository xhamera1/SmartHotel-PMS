"""Offline holdout evaluation, baseline comparison, and figure generation."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np
import pandas as pd
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
) -> EvaluationResult:
    """Evaluate the selected RF from Step 2 without retraining on test data."""

    return evaluate_holdout(
        random_forest=training.best_pipeline,
        split=training.split,
        output_dir=output_dir,
        permutation_repeats=permutation_repeats,
        random_state=random_state,
        n_jobs=n_jobs,
        feature_names=training.feature_names,
    )


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
