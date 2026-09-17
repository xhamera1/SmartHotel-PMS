"""Tests for datagen config validation and CLI output (Phase 4 step 1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from datagen.cli import main
from datagen.config import DatagenConfig

CONFIGS = Path(__file__).resolve().parents[2] / "datagen" / "configs"


def test_default_yaml_loads() -> None:
    config = DatagenConfig.from_yaml(CONFIGS / "default.yaml")
    assert config.seed == 42
    assert len(config.hotel.room_types) == 3
    assert len(config.demand.weekday_multipliers) == 7
    assert abs(sum(p.share for p in config.events.categories.values()) - 1.0) < 1e-9


def test_tiny_yaml_loads() -> None:
    config = DatagenConfig.from_yaml(CONFIGS / "tiny.yaml")
    assert config.seed == 7
    assert config.horizon.start.isoformat() == "2024-06-01"


def test_config_hash_stable() -> None:
    a = DatagenConfig.from_yaml(CONFIGS / "tiny.yaml")
    b = DatagenConfig.from_yaml(CONFIGS / "tiny.yaml")
    assert a.config_hash() == b.config_hash()
    assert len(a.config_hash()) == 64


def test_rejects_bad_price_band() -> None:
    raw = DatagenConfig.from_yaml(CONFIGS / "tiny.yaml").model_dump(mode="json")
    raw["hotel"]["room_types"][0]["min_price"] = 500
    raw["hotel"]["room_types"][0]["base_price"] = 250
    with pytest.raises(ValidationError, match="min_price"):
        DatagenConfig.model_validate(raw)


def test_rejects_event_shares_not_one() -> None:
    raw = DatagenConfig.from_yaml(CONFIGS / "tiny.yaml").model_dump(mode="json")
    raw["events"]["categories"]["MUSIC"]["share"] = 0.9
    with pytest.raises(ValidationError, match="sum to 1"):
        DatagenConfig.model_validate(raw)


def test_cli_run_writes_parquet_and_metadata(tmp_path: Path) -> None:
    output = tmp_path / "run"
    code = main(["run", "--config", str(CONFIGS / "tiny.yaml"), "--output", str(output)])
    assert code == 0

    for name in ("calendar", "events", "nights", "bookings", "snapshots"):
        assert (output / f"{name}.parquet").is_file()

    meta = json.loads((output / "metadata.json").read_text(encoding="utf-8"))
    assert meta["seed"] == 7
    assert meta["config_hash"] == DatagenConfig.from_yaml(CONFIGS / "tiny.yaml").config_hash()
    assert meta["row_counts"]["calendar"] == 14
    assert meta["row_counts"]["events"] == 0
    assert meta["row_counts"]["nights"] == 0
    assert meta["row_counts"]["bookings"] == 0
    assert meta["row_counts"]["snapshots"] == 0
    assert set(meta["files"]) == {"calendar", "events", "nights", "bookings", "snapshots"}
