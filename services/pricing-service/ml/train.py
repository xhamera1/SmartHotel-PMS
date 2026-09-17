"""End-to-end offline training command for versioned model artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ml.artifacts import DEFAULT_MODEL_ROOT, save_model_artifact
from ml.evaluation import evaluate_training_result
from ml.pipeline import TrainingConfig, tune_random_forest
from ml.registry import register_artifact

PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[2]
DEFAULT_DATASET = REPO_ROOT / "artifacts" / "datasets" / "default" / "snapshots.parquet"
DEFAULT_EVALUATION_ROOT = REPO_ROOT / "artifacts" / "evaluation"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train and persist a pricing model")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_MODEL_ROOT)
    parser.add_argument("--evaluation-output", type=Path, default=DEFAULT_EVALUATION_ROOT)
    parser.add_argument("--version")
    parser.add_argument("--search-iterations", type=int, default=30)
    parser.add_argument("--cv-splits", type=int, default=5)
    parser.add_argument("--n-jobs", type=int, default=1)
    parser.add_argument("--permutation-repeats", type=int, default=10)
    parser.add_argument(
        "--register-database-url",
        help="If provided, insert the new artifact into pricing.model_registry",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.dataset.is_file():
        raise SystemExit(f"dataset not found: {args.dataset}")
    config = TrainingConfig(
        cv_splits=args.cv_splits,
        search_iterations=args.search_iterations,
        n_jobs=args.n_jobs,
    )
    training = tune_random_forest(pd.read_parquet(args.dataset), config=config)
    evaluation = evaluate_training_result(
        training,
        output_dir=args.evaluation_output,
        permutation_repeats=args.permutation_repeats,
        random_state=config.random_state,
        n_jobs=config.n_jobs,
    )
    artifact = save_model_artifact(
        training,
        evaluation,
        dataset_path=args.dataset,
        artifact_root=args.artifact_root,
        version=args.version,
    )
    if args.register_database_url:
        register_artifact(args.register_database_url, artifact.metadata_path)
    print(f"model={artifact.model_path}")
    print(f"metadata={artifact.metadata_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised as a CLI
    raise SystemExit(main())
