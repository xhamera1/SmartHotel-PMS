"""Tests for pandera data contracts and EDA helpers (Phase 4 step 7)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pandera.errors as pa_errors
import pytest

from datagen.cli import main
from datagen.config import DatagenConfig
from datagen.schemas import BookingsSchema, CalendarSchema, NightsSchema
from datagen.tables import empty_datasets
from datagen.validate import DatasetValidationError, validate_datasets

CONFIGS = Path(__file__).resolve().parents[2] / "datagen" / "configs"


@pytest.fixture
def tiny_config() -> DatagenConfig:
    return DatagenConfig.from_yaml(CONFIGS / "tiny.yaml")


def test_validate_datasets_passes_on_tiny_cli(tmp_path: Path) -> None:
    output = tmp_path / "run"
    assert main(["run", "--config", str(CONFIGS / "tiny.yaml"), "--output", str(output)]) == 0
    report = json.loads((output / "validation_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "passed"
    meta = json.loads((output / "metadata.json").read_text(encoding="utf-8"))
    assert meta["validation_status"] == "passed"


def test_validate_rejects_duplicate_calendar_dates() -> None:
    datasets = empty_datasets()
    datasets["calendar"] = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-06-01", "2024-06-01"]),
            "season_factor": [1.0, 1.0],
            "weekday_factor": [1.0, 1.0],
            "holiday_flag": [0, 0],
            "bridge_flag": [0, 0],
            "holiday_factor": [1.0, 1.0],
            "calendar_factor": [1.0, 1.0],
        }
    )
    # Fill other tables with one valid-ish empty-allowed; only calendar non-empty fails.
    with pytest.raises(DatasetValidationError) as exc:
        validate_datasets(datasets)
    assert exc.value.report.tables[0].status == "failed" or any(
        t.name == "calendar" and t.status == "failed" for t in exc.value.report.tables
    )


def test_nights_schema_rejects_non_positive_price() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-06-01"]),
            "room_type": ["STD"],
            "base_price": [250.0],
            "demand_latent": [10.0],
            "event_uplift": [0.0],
            "optimal_price": [0.0],
            "price_multiplier": [0.0],
        }
    )
    with pytest.raises((pa_errors.SchemaError, pa_errors.SchemaErrors)):
        NightsSchema.validate(frame, lazy=True)


def test_bookings_schema_rejects_checkout_before_checkin() -> None:
    frame = pd.DataFrame(
        {
            "booking_id": ["B1"],
            "room_type": ["STD"],
            "check_in": pd.to_datetime(["2024-06-02"]),
            "check_out": pd.to_datetime(["2024-06-01"]),
            "booked_at": pd.to_datetime(["2024-05-01"]),
            "nights": [1],
            "price_total": [250.0],
            "cancelled": [False],
        }
    )
    with pytest.raises((pa_errors.SchemaError, pa_errors.SchemaErrors)):
        BookingsSchema.validate(frame, lazy=True)


def test_calendar_schema_ok_minimal() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-06-01"]),
            "season_factor": [1.1],
            "weekday_factor": [1.0],
            "holiday_flag": [0],
            "bridge_flag": [0],
            "holiday_factor": [1.0],
            "calendar_factor": [1.1],
        }
    )
    CalendarSchema.validate(frame)


def test_eda_writes_all_figures(tmp_path: Path, tiny_config: DatagenConfig) -> None:
    pytest.importorskip("matplotlib.pyplot")
    data_dir = tmp_path / "data"
    fig_dir = tmp_path / "figs"
    assert main(["run", "--config", str(CONFIGS / "tiny.yaml"), "--output", str(data_dir)]) == 0
    rooms = {rt.code: rt.rooms for rt in tiny_config.hotel.room_types}
    from datagen.eda import run_eda

    result = run_eda(dataset_dir=data_dir, figures_dir=fig_dir, rooms_by_type=rooms)
    assert set(result.figure_paths) == {
        "seasonal_decomposition",
        "occupancy_histogram",
        "price_demand_scatter",
        "correlation_heatmap",
        "event_uplift",
    }
    for path in result.figure_paths.values():
        assert path.is_file()
        assert path.stat().st_size > 0
    assert 0.0 <= result.occupancy_mean <= 1.0


def test_eda_cli(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib.pyplot")
    data_dir = tmp_path / "data"
    fig_dir = tmp_path / "figs"
    assert main(["run", "--config", str(CONFIGS / "tiny.yaml"), "--output", str(data_dir)]) == 0
    assert (
        main(
            [
                "eda",
                "--config",
                str(CONFIGS / "tiny.yaml"),
                "--input",
                str(data_dir),
                "--figures",
                str(fig_dir),
            ]
        )
        == 0
    )
    assert (fig_dir / "occupancy_histogram.png").is_file()


def test_nightly_occupancy_bounds(tiny_config: DatagenConfig, tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    assert main(["run", "--config", str(CONFIGS / "tiny.yaml"), "--output", str(data_dir)]) == 0
    nights = pd.read_parquet(data_dir / "nights.parquet")
    bookings = pd.read_parquet(data_dir / "bookings.parquet")
    rooms = {rt.code: rt.rooms for rt in tiny_config.hotel.room_types}
    from datagen.eda import nightly_occupancy

    occ = nightly_occupancy(bookings, nights, rooms)
    assert occ["occupancy"].between(0.0, 1.0).all()
