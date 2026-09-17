"""Unit tests for calendar demand factors (Phase 4 step 2)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from datagen.calendar import (
    DEFAULT_BRIDGE_RATIO,
    build_calendar_frame,
    holiday_factor,
    holiday_set_for_horizon,
    is_bridge_day,
    is_polish_holiday,
    season_factor,
    weekday_factor,
)
from datagen.config import DatagenConfig, DemandConfig

CONFIGS = Path(__file__).resolve().parents[2] / "datagen" / "configs"


@pytest.fixture
def demand() -> DemandConfig:
    return DatagenConfig.from_yaml(CONFIGS / "tiny.yaml").demand


def test_season_factor_positive_and_bounded(demand: DemandConfig) -> None:
    amp = demand.season_amplitude
    samples = [season_factor(date(2024, m, 15), amp) for m in range(1, 13)]
    assert all(v > 0 for v in samples)
    # With amplitude 0.35, values stay in a sensible band around 1.
    assert min(samples) >= 1.0 - amp - 1e-9
    assert max(samples) <= 1.0 + amp + amp * 0.6 + 1e-6


def test_season_factor_summer_above_spring(demand: DemandConfig) -> None:
    amp = demand.season_amplitude
    july = season_factor(date(2024, 7, 15), amp)
    april = season_factor(date(2024, 4, 15), amp)
    assert july > april


def test_season_factor_december_peak(demand: DemandConfig) -> None:
    amp = demand.season_amplitude
    late_dec = season_factor(date(2024, 12, 27), amp)
    mid_nov = season_factor(date(2024, 11, 15), amp)
    assert late_dec > mid_nov


def test_weekday_factor_matches_table(demand: DemandConfig) -> None:
    # 2024-06-03 = Monday ... 2024-06-09 = Sunday
    for offset, expected in enumerate(demand.weekday_multipliers):
        day = date(2024, 6, 3 + offset)
        assert day.weekday() == offset
        assert weekday_factor(day, demand.weekday_multipliers) == expected

    friday = date(2024, 6, 7)
    saturday = date(2024, 6, 8)
    tuesday = date(2024, 6, 4)
    assert weekday_factor(friday, demand.weekday_multipliers) > weekday_factor(
        tuesday, demand.weekday_multipliers
    )
    assert weekday_factor(saturday, demand.weekday_multipliers) == max(demand.weekday_multipliers)


def test_polish_holidays_known_dates() -> None:
    holidays_2024 = holiday_set_for_horizon(date(2024, 1, 1), date(2024, 12, 31))
    assert is_polish_holiday(date(2024, 1, 1), holidays_2024)
    assert is_polish_holiday(date(2024, 5, 1), holidays_2024)
    assert is_polish_holiday(date(2024, 5, 3), holidays_2024)
    assert is_polish_holiday(date(2024, 11, 11), holidays_2024)
    assert is_polish_holiday(date(2024, 12, 25), holidays_2024)
    assert not is_polish_holiday(date(2024, 6, 12), holidays_2024)


def test_bridge_day_after_thursday_holiday() -> None:
    # Synthetic Thursday holiday → Friday is the bridge day.
    thursday = date(2024, 5, 2)
    friday = date(2024, 5, 3)
    holiday_dates = frozenset({thursday})
    assert is_bridge_day(friday, holiday_dates)
    assert not is_bridge_day(thursday, holiday_dates)


def test_bridge_day_before_tuesday_holiday() -> None:
    tuesday = date(2024, 6, 4)
    monday = date(2024, 6, 3)
    holiday_dates = frozenset({tuesday})
    assert is_bridge_day(monday, holiday_dates)


def test_holiday_factor_boosts(demand: DemandConfig) -> None:
    holidays_2024 = holiday_set_for_horizon(date(2024, 1, 1), date(2024, 12, 31))
    mult, is_hol, is_br = holiday_factor(
        date(2024, 11, 11),
        demand.holiday_boost,
        holidays_2024,
    )
    assert is_hol and not is_br
    assert mult == pytest.approx(1.0 + demand.holiday_boost)

    # Bridge: Friday after synthetic Thursday holiday
    thursday = date(2024, 6, 6)
    friday = date(2024, 6, 7)
    synthetic = frozenset({thursday})
    mult_b, is_hol_b, is_br_b = holiday_factor(
        friday,
        demand.holiday_boost,
        synthetic,
        bridge_ratio=DEFAULT_BRIDGE_RATIO,
    )
    assert not is_hol_b and is_br_b
    assert mult_b == pytest.approx(1.0 + demand.holiday_boost * DEFAULT_BRIDGE_RATIO)


def test_build_calendar_frame_covers_horizon() -> None:
    config = DatagenConfig.from_yaml(CONFIGS / "tiny.yaml")
    frame = build_calendar_frame(config.horizon, config.demand)
    expected_days = (config.horizon.end - config.horizon.start).days + 1
    assert len(frame) == expected_days
    assert list(frame.columns) == [
        "date",
        "season_factor",
        "weekday_factor",
        "holiday_flag",
        "bridge_flag",
        "holiday_factor",
        "calendar_factor",
    ]
    assert (frame["season_factor"] > 0).all()
    assert (frame["weekday_factor"] > 0).all()
    assert (frame["calendar_factor"] > 0).all()
    # holiday and bridge mutually exclusive
    assert not ((frame["holiday_flag"] == 1) & (frame["bridge_flag"] == 1)).any()


def test_pipeline_writes_calendar_rows(tmp_path) -> None:
    from datagen.cli import main

    output = tmp_path / "run"
    code = main(["run", "--config", str(CONFIGS / "tiny.yaml"), "--output", str(output)])
    assert code == 0
    import pandas as pd

    calendar = pd.read_parquet(output / "calendar.parquet")
    assert len(calendar) == 14  # 2024-06-01 .. 2024-06-14 inclusive
