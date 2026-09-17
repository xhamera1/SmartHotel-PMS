"""Write parquet tables and the JSON metadata sidecar."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from datagen.config import DatagenConfig
from datagen.tables import DATASET_NAMES


@dataclass(frozen=True)
class WriteResult:
    output_dir: Path
    metadata_path: Path
    row_counts: dict[str, int]
    config_hash: str


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

    row_counts: dict[str, int] = {}
    files: dict[str, str] = {}
    for name in DATASET_NAMES:
        filename = f"{name}.parquet"
        path = output_dir / filename
        datasets[name].to_parquet(path, index=False)
        row_counts[name] = int(len(datasets[name]))
        files[name] = filename

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
    }
    metadata_path = output_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    return WriteResult(
        output_dir=output_dir,
        metadata_path=metadata_path,
        row_counts=row_counts,
        config_hash=metadata["config_hash"],
    )
