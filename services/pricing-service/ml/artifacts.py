"""Versioned, reproducible model artifact persistence."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import joblib

from ml.evaluation import EvaluationResult
from ml.features import FEATURE_SCHEMA_HASH, feature_schema_payload
from ml.pipeline import TrainingResult

MODEL_FILENAME = "model.joblib"
METADATA_FILENAME = "metadata.json"
PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[2]
DEFAULT_MODEL_ROOT = REPO_ROOT / "artifacts" / "models"
_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class ModelArtifact:
    version: str
    directory: Path
    model_path: Path
    metadata_path: Path
    metadata: dict[str, object]


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Hash the exact dataset bytes used for training."""

    if not path.is_file():
        raise FileNotFoundError(path)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def current_git_sha(repo_root: Path = REPO_ROOT) -> str:
    """Return the immutable source revision recorded with a model."""

    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    sha = completed.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise RuntimeError(f"git returned an invalid SHA: {sha!r}")
    return sha


def default_model_version(*, git_sha: str, trained_at: datetime) -> str:
    timestamp = trained_at.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"rf-{timestamp}-{git_sha[:8]}"


def save_model_artifact(
    training: TrainingResult,
    evaluation: EvaluationResult,
    *,
    dataset_path: Path,
    artifact_root: Path = DEFAULT_MODEL_ROOT,
    version: str | None = None,
    git_sha: str | None = None,
    trained_at: datetime | None = None,
) -> ModelArtifact:
    """Persist the fitted sklearn pipeline and its complete provenance sidecar."""

    timestamp = trained_at or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("trained_at must be timezone-aware")
    source_sha = git_sha or current_git_sha()
    model_version = version or default_model_version(git_sha=source_sha, trained_at=timestamp)
    if not _VERSION_PATTERN.fullmatch(model_version):
        raise ValueError(
            "version must start with an alphanumeric and contain only letters, "
            "digits, '.', '_' or '-'"
        )

    artifact_dir = artifact_root / model_version
    artifact_dir.mkdir(parents=True, exist_ok=False)
    model_path = artifact_dir / MODEL_FILENAME
    metadata_path = artifact_dir / METADATA_FILENAME
    joblib.dump(training.best_pipeline, model_path)

    metadata: dict[str, object] = {
        "version": model_version,
        "algorithm": "RandomForestRegressor",
        "artifact_path": _portable_path(model_path),
        "dataset_path": _portable_path(dataset_path),
        "dataset_hash": sha256_file(dataset_path),
        "feature_schema_hash": FEATURE_SCHEMA_HASH,
        "feature_schema": feature_schema_payload(),
        "git_sha": source_sha,
        "trained_at": timestamp.astimezone(UTC).isoformat(),
        "config": {
            "training": asdict(training.config),
            "model_features": list(training.feature_names),
            "best_params": training.search.best_params_,
        },
        "metrics": evaluation.metrics,
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return ModelArtifact(
        version=model_version,
        directory=artifact_dir,
        model_path=model_path,
        metadata_path=metadata_path,
        metadata=metadata,
    )


def load_artifact_metadata(path: Path) -> dict[str, object]:
    """Load and minimally validate a metadata sidecar before registry insertion."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid artifact metadata JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("artifact metadata must be a JSON object")
    required = {
        "version",
        "algorithm",
        "artifact_path",
        "dataset_hash",
        "config",
        "metrics",
        "feature_schema_hash",
        "git_sha",
        "trained_at",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"artifact metadata missing fields: {missing}")
    if payload["feature_schema_hash"] != FEATURE_SCHEMA_HASH:
        raise ValueError("artifact feature_schema_hash does not match the running code")
    return payload


def _portable_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(resolved)
