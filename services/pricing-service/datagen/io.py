"""Write parquet tables, pandera validation report, and JSON metadata sidecar."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from datagen.config import DatagenConfig
from datagen.tables import DATASET_NAMES
from datagen.validate import DatasetValidationError, ValidationReport, validate_datasets


@dataclass(frozen=True)
class WriteResult:
    output_dir: Path
    metadata_path: Path
    validation_path: Path
    row_counts: dict[str, int]
    config_hash: str
    validation: ValidationReport


def write_dataset_bundle(
    *,
    config: DatagenConfig,
    config_path: Path,
    datasets: dict[str, pd.DataFrame],
    output_dir: Path,
    generator_version: str = "0.1.0",
) -> WriteResult:
    output_dir.mkdir(parents=True, exist_ok=True)

    missing = [name for name in DATASET_NAMES if name not in datasets]
    if missing:
        msg = f"missing datasets: {missing}"
        raise KeyError(msg)

    validation_path = output_dir / "validation_report.json"
    try:
        validation = validate_datasets(datasets)
    except DatasetValidationError as exc:
        exc.report.write_json(validation_path)
        raise

    row_counts: dict[str, int] = {}
    files: dict[str, str] = {}
    for name in DATASET_NAMES:
        filename = f"{name}.parquet"
        path = output_dir / filename
        datasets[name].to_parquet(path, index=False)
        row_counts[name] = int(len(datasets[name]))
        files[name] = filename

    validation.write_json(validation_path)

    metadata = {
        "generator_version": generator_version,
        "generated_at": datetime.now(UTC).isoformat(),
        "seed": config.seed,
        "config_hash": config.config_hash(),
        "config_path": str(config_path.resolve()),
        "horizon": {
            "start": config.horizon.start.isoformat(),
            "end": config.horizon.end.isoformat(),
        },
        "row_counts": row_counts,
        "files": files,
        "validation_status": validation.status,
        "validation_report": validation_path.name,
    }
    metadata_path = output_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    return WriteResult(
        output_dir=output_dir,
        metadata_path=metadata_path,
        validation_path=validation_path,
        row_counts=row_counts,
        config_hash=metadata["config_hash"],
        validation=validation,
    )
