"""Tests for the synthetic event catalog (Phase 4 step 3)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from datagen.cli import main
from datagen.config import DatagenConfig
from datagen.events import (
    expected_event_count,
    generate_events,
    true_demand_uplift,
)
from datagen.pipeline import seed_rng

CONFIGS = Path(__file__).resolve().parents[2] / "datagen" / "configs"


@pytest.fixture
def default_config() -> DatagenConfig:
    return DatagenConfig.from_yaml(CONFIGS / "default.yaml")


@pytest.fixture
def tiny_config() -> DatagenConfig:
    return DatagenConfig.from_yaml(CONFIGS / "tiny.yaml")


def test_expected_event_count_scales_with_horizon(default_config: DatagenConfig) -> None:
    n = expected_event_count(default_config.horizon, default_config.events.per_year)
    # ~3 years × 60 ≈ 180 (E3 corpus size in the plan)
    assert 170 <= n <= 190


def test_true_uplift_monotonic_in_attendance() -> None:
    near = true_demand_uplift(attendance=5_000, distance_km=2.0, uplift_per_10k=0.25)
    far_size = true_demand_uplift(attendance=20_000, distance_km=2.0, uplift_per_10k=0.25)
    assert far_size > near


def test_true_uplift_decays_with_distance() -> None:
    close = true_demand_uplift(attendance=10_000, distance_km=1.0, uplift_per_10k=0.25)
    far = true_demand_uplift(attendance=10_000, distance_km=12.0, uplift_per_10k=0.25)
    assert close > far > 0


def test_generate_events_deterministic(tiny_config: DatagenConfig) -> None:
    a = generate_events(tiny_config, seed_rng(tiny_config.seed))
    b = generate_events(tiny_config, seed_rng(tiny_config.seed))
    assert [(e.event_id, e.name, e.true_uplift, e.attendance) for e in a] == [
        (e.event_id, e.name, e.true_uplift, e.attendance) for e in b
    ]


def test_generate_events_schema_and_bounds(tiny_config: DatagenConfig) -> None:
    events = generate_events(tiny_config, seed_rng(tiny_config.seed))
    assert len(events) == expected_event_count(tiny_config.horizon, tiny_config.events.per_year)
    assert len(events) >= 1

    for event in events:
        profile = tiny_config.events.categories[event.category]
        assert profile.attendance[0] <= event.attendance <= profile.attendance[1]
        assert 0.3 <= event.distance_km <= 25.0
        assert event.start_date <= event.end_date
        assert tiny_config.horizon.start <= event.start_date <= tiny_config.horizon.end
        assert tiny_config.horizon.start <= event.end_date <= tiny_config.horizon.end
        duration = (event.end_date - event.start_date).days + 1
        assert 1 <= duration <= 3
        assert event.name
        assert event.description
        assert f"{event.attendance:,}" in event.description
        assert event.true_uplift == pytest.approx(
            true_demand_uplift(
                attendance=event.attendance,
                distance_km=event.distance_km,
                uplift_per_10k=profile.uplift_per_10k,
            )
        )


def test_category_mix_roughly_follows_shares(default_config: DatagenConfig) -> None:
    events = generate_events(default_config, seed_rng(default_config.seed))
    counts: dict[str, int] = {}
    for event in events:
        counts[event.category] = counts.get(event.category, 0) + 1
    total = len(events)
    for category, profile in default_config.events.categories.items():
        share = counts.get(category, 0) / total
        # Loose band — multinomial noise over ~180 draws.
        assert abs(share - profile.share) < 0.12


def test_cli_writes_events_parquet(tmp_path: Path, tiny_config: DatagenConfig) -> None:
    output = tmp_path / "run"
    assert main(["run", "--config", str(CONFIGS / "tiny.yaml"), "--output", str(output)]) == 0
    frame = pd.read_parquet(output / "events.parquet")
    expected = expected_event_count(tiny_config.horizon, tiny_config.events.per_year)
    assert len(frame) == expected
    assert set(frame.columns) >= {
        "event_id",
        "category",
        "name",
        "description",
        "start_date",
        "end_date",
        "attendance",
        "distance_km",
        "true_uplift",
    }
