"""PostgreSQL model registry operations and promotion CLI."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import sqlalchemy as sa

from ml.artifacts import load_artifact_metadata

DATABASE_ENV = "PRICING_DATABASE_URL"


def register_artifact(database_url: str, metadata_path: Path) -> None:
    """Insert one inactive registry row from a validated artifact sidecar."""

    metadata = load_artifact_metadata(metadata_path)
    statement = sa.text(
        """
        INSERT INTO pricing.model_registry (
            version, algorithm, dataset_hash, params, metrics,
            feature_schema_hash, artifact_path, trained_at, is_active
        ) VALUES (
            :version, :algorithm, :dataset_hash, CAST(:params AS jsonb),
            CAST(:metrics AS jsonb), :feature_schema_hash, :artifact_path,
            :trained_at, false
        )
        """
    )
    values = {
        "version": metadata["version"],
        "algorithm": metadata["algorithm"],
        "dataset_hash": metadata["dataset_hash"],
        "params": json.dumps(metadata["config"], sort_keys=True, allow_nan=False),
        "metrics": json.dumps(metadata["metrics"], sort_keys=True, allow_nan=False),
        "feature_schema_hash": metadata["feature_schema_hash"],
        "artifact_path": metadata["artifact_path"],
        "trained_at": metadata["trained_at"],
    }
    engine = sa.create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(statement, values)
    finally:
        engine.dispose()


def promote_model(database_url: str, version: str) -> None:
    """Atomically make ``version`` the sole active model."""

    engine = sa.create_engine(database_url)
    try:
        with engine.begin() as connection:
            exists = connection.execute(
                sa.text("SELECT 1 FROM pricing.model_registry WHERE version = :version FOR UPDATE"),
                {"version": version},
            ).scalar_one_or_none()
            if exists is None:
                raise ValueError(f"model version not found: {version}")
            connection.execute(
                sa.text("UPDATE pricing.model_registry SET is_active = false WHERE is_active")
            )
            connection.execute(
                sa.text(
                    "UPDATE pricing.model_registry SET is_active = true WHERE version = :version"
                ),
                {"version": version},
            )
    finally:
        engine.dispose()


def _database_url(cli_value: str | None) -> str:
    value = cli_value or os.environ.get(DATABASE_ENV)
    if not value:
        raise ValueError(f"database URL required via --database-url or {DATABASE_ENV}")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the pricing model registry")
    subparsers = parser.add_subparsers(dest="command", required=True)

    register = subparsers.add_parser("register", help="Register an artifact as inactive")
    register.add_argument("--metadata", type=Path, required=True)
    register.add_argument("--database-url")

    promote = subparsers.add_parser("promote", help="Promote one registered model")
    promote.add_argument("--version", required=True)
    promote.add_argument("--database-url")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        database_url = _database_url(args.database_url)
        if args.command == "register":
            register_artifact(database_url, args.metadata)
            print(f"registered={args.metadata}")
        else:
            promote_model(database_url, args.version)
            print(f"active_model={args.version}")
    except (OSError, ValueError, sa.SQLAlchemyError) as exc:
        print(f"registry_error={exc}")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised as a CLI
    raise SystemExit(main())
