"""RQ2 event-feature ablation with machine-generated comparison tables."""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ml.baselines import RANDOM_FOREST_MODEL
from ml.evaluation import EvaluationResult, evaluate_training_result
from ml.features import EVENT_FEATURES, FEATURE_NAMES, NON_EVENT_FEATURES
from ml.pipeline import TrainingConfig, tune_random_forest

WITH_EVENTS = "with_event_features"
WITHOUT_EVENTS = "without_event_features"
COMPARISON_JSON = "ablation_comparison.json"
COMPARISON_CSV = "ablation_comparison.csv"
COMPARISON_MARKDOWN = "ablation_comparison.md"

PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[2]
DEFAULT_DATASET = REPO_ROOT / "artifacts" / "datasets" / "default" / "snapshots.parquet"
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "experiments" / "event-ablation"


@dataclass(frozen=True)
class AblationResult:
    evaluations: dict[str, EvaluationResult]
    comparison: dict[str, object]
    comparison_paths: dict[str, Path]


def run_event_ablation(
    snapshots: pd.DataFrame,
    *,
    output_dir: Path,
    config: TrainingConfig | None = None,
    permutation_repeats: int = 10,
    param_distributions: Mapping[str, Sequence[object]] | None = None,
) -> AblationResult:
    """Train/evaluate otherwise-identical RFs with and without event signals."""

    training_config = config or TrainingConfig()
    output_dir.mkdir(parents=True, exist_ok=True)
    evaluations: dict[str, EvaluationResult] = {}
    feature_sets = {
        WITH_EVENTS: FEATURE_NAMES,
        WITHOUT_EVENTS: NON_EVENT_FEATURES,
    }
    for run_name, feature_names in feature_sets.items():
        training = tune_random_forest(
            snapshots,
            config=training_config,
            feature_names=feature_names,
            param_distributions=param_distributions,
        )
        evaluations[run_name] = evaluate_training_result(
            training,
            output_dir=output_dir / run_name,
            permutation_repeats=permutation_repeats,
            random_state=training_config.random_state,
            n_jobs=training_config.n_jobs,
        )

    comparison = build_ablation_comparison(
        evaluations[WITH_EVENTS].metrics,
        evaluations[WITHOUT_EVENTS].metrics,
    )
    paths = {
        "json": output_dir / COMPARISON_JSON,
        "csv": output_dir / COMPARISON_CSV,
        "markdown": output_dir / COMPARISON_MARKDOWN,
    }
    _write_comparison(comparison, paths)
    return AblationResult(
        evaluations=evaluations,
        comparison=comparison,
        comparison_paths=paths,
    )


def build_ablation_comparison(
    with_events_metrics: Mapping[str, object],
    without_events_metrics: Mapping[str, object],
) -> dict[str, object]:
    """Build RQ2 rows; positive gain always means event features helped."""

    with_overall = _rf_overall(with_events_metrics)
    without_overall = _rf_overall(without_events_metrics)
    rows: list[dict[str, object]] = []
    for target in ("multiplier", "price_pln"):
        for metric in ("mae", "rmse", "r2", "mape"):
            with_value = float(with_overall[target][metric])
            without_value = float(without_overall[target][metric])
            higher_is_better = metric == "r2"
            gain = with_value - without_value if higher_is_better else without_value - with_value
            relative_gain = None
            if without_value != 0:
                denominator = abs(without_value)
                relative_gain = gain / denominator * 100.0
            rows.append(
                {
                    "target": target,
                    "metric": metric,
                    WITH_EVENTS: with_value,
                    WITHOUT_EVENTS: without_value,
                    "event_feature_gain": gain,
                    "relative_gain_percent": relative_gain,
                    "event_features_improve": gain > 0,
                }
            )
    return {
        "question": "RQ2: do event-pipeline features improve pricing accuracy?",
        "dropped_features": list(EVENT_FEATURES),
        "gain_definition": (
            "positive means with-event is better; without-with for errors, with-without for R2"
        ),
        "rows": rows,
    }


def _rf_overall(metrics: Mapping[str, object]) -> dict[str, dict[str, float]]:
    models = metrics.get("models")
    if not isinstance(models, dict):
        raise ValueError("metrics missing models")
    random_forest = models.get(RANDOM_FOREST_MODEL)
    if not isinstance(random_forest, dict):
        raise ValueError("metrics missing random_forest")
    overall = random_forest.get("overall")
    if not isinstance(overall, dict):
        raise ValueError("metrics missing random_forest overall metrics")
    return overall  # type: ignore[return-value]


def _write_comparison(comparison: dict[str, object], paths: dict[str, Path]) -> None:
    paths["json"].write_text(
        json.dumps(comparison, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    rows = comparison["rows"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("ablation comparison has no rows")
    columns = list(rows[0])
    with paths["csv"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_markdown_value(row[column]) for column in columns) + " |" for row in rows
    ]
    paths["markdown"].write_text(
        "# Event-feature ablation (RQ2)\n\n" + "\n".join([header, separator, *body]) + "\n",
        encoding="utf-8",
    )


def _markdown_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return "n/a"
    return str(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the RQ2 event-feature ablation")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--search-iterations", type=int, default=30)
    parser.add_argument("--cv-splits", type=int, default=5)
    parser.add_argument("--n-jobs", type=int, default=1)
    parser.add_argument("--permutation-repeats", type=int, default=10)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.dataset.is_file():
        raise SystemExit(f"dataset not found: {args.dataset}")
    result = run_event_ablation(
        pd.read_parquet(args.dataset),
        output_dir=args.output,
        config=TrainingConfig(
            cv_splits=args.cv_splits,
            search_iterations=args.search_iterations,
            n_jobs=args.n_jobs,
        ),
        permutation_repeats=args.permutation_repeats,
    )
    print(f"comparison={result.comparison_paths['markdown']}")
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised as a CLI
    raise SystemExit(main())
