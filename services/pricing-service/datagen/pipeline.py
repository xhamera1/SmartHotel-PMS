"""Datagen orchestration — calendar, events, demand & bookings."""

from __future__ import annotations

import random
from pathlib import Path

import numpy as np

from datagen.calendar import build_calendar_frame
from datagen.config import DatagenConfig
from datagen.demand import build_night_demands, nights_to_frame, simulate_bookings
from datagen.events import events_to_frame, generate_events
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
    rng = seed_rng(config.seed)
    datasets = empty_datasets()
    datasets["calendar"] = build_calendar_frame(config.horizon, config.demand)
    events = generate_events(config, rng)
    datasets["events"] = events_to_frame(events)
    night_demands = build_night_demands(config, datasets["calendar"], events, rng)
    datasets["nights"] = nights_to_frame(night_demands)
    datasets["bookings"] = simulate_bookings(config, night_demands, rng)
    return write_dataset_bundle(
        config=config,
        config_path=config_path,
        datasets=datasets,
        output_dir=output_dir,
    )
