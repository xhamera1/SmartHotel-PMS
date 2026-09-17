"""Datagen orchestration — step 2 fills calendar factors; later steps add the rest."""

from __future__ import annotations

import random
from pathlib import Path

import numpy as np

from datagen.calendar import build_calendar_frame
from datagen.config import DatagenConfig
from datagen.io import WriteResult, write_dataset_bundle
from datagen.tables import empty_datasets


def seed_rng(seed: int) -> np.random.Generator:
    """Single global seed for Python + NumPy RNGs used by later simulation steps."""
    random.seed(seed)
    return np.random.default_rng(seed)


def run_generation(
    *,
    config: DatagenConfig,
    config_path: Path,
    output_dir: Path,
) -> WriteResult:
    seed_rng(config.seed)
    datasets = empty_datasets()
    datasets["calendar"] = build_calendar_frame(config.horizon, config.demand)
    return write_dataset_bundle(
        config=config,
        config_path=config_path,
        datasets=datasets,
        output_dir=output_dir,
    )
