"""Tests for latent demand and booking simulation (Phase 4 step 4)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from datagen.calendar import build_calendar_frame
from datagen.cli import main
from datagen.config import DatagenConfig
from datagen.demand import (
    BASE_ATTEMPTS_PER_ROOM,
    build_night_demands,
    conversion_probability,
    event_uplift_by_date,
    latent_demand,
    simulate_bookings,
)
from datagen.events import SyntheticEvent, generate_events
from datagen.pipeline import seed_rng

CONFIGS = Path(__file__).resolve().parents[2] / "datagen" / "configs"


@pytest.fixture
def tiny_config() -> DatagenConfig:
    return DatagenConfig.from_yaml(CONFIGS / "tiny.yaml")


def test_latent_demand_formula() -> None:
    d = latent_demand(
        rooms=10,
        season=1.2,
        weekday=1.1,
        holiday=1.0,
        event_uplift=0.5,
        eps=0.0,
    )
    expected = 10 * BASE_ATTEMPTS_PER_ROOM * 1.2 * 1.1 * 1.0 * 1.5 * 1.0
    assert d == pytest.approx(expected)


def test_latent_demand_increases_with_event_uplift() -> None:
    low = latent_demand(rooms=10, season=1.0, weekday=1.0, holiday=1.0, event_uplift=0.0, eps=0.0)
    high = latent_demand(rooms=10, season=1.0, weekday=1.0, holiday=1.0, event_uplift=0.4, eps=0.0)
    assert high > low


def test_conversion_at_wtp_is_half() -> None:
    assert conversion_probability(250.0, 250.0, elasticity=1.6) == pytest.approx(0.5)


def test_conversion_falls_when_price_above_wtp() -> None:
    cheap = conversion_probability(200.0, 250.0, elasticity=1.6)
    expensive = conversion_probability(300.0, 250.0, elasticity=1.6)
    assert cheap > 0.5 > expensive


def test_higher_elasticity_sharper_penalty() -> None:
    mild = conversion_probability(300.0, 250.0, elasticity=1.1)
    sharp = conversion_probability(300.0, 250.0, elasticity=1.6)
    assert sharp < mild


def test_event_uplift_by_date_sums_overlaps() -> None:
    events = [
        SyntheticEvent(
            event_id="EVT-0001",
            category="MUSIC",
            name="A",
            description="A",
            start_date=date(2024, 6, 1),
            end_date=date(2024, 6, 2),
            attendance=10_000,
            distance_km=2.0,
            true_uplift=0.2,
            venue="Tauron Arena",
        ),
        SyntheticEvent(
            event_id="EVT-0002",
            category="CULTURE",
            name="B",
            description="B",
            start_date=date(2024, 6, 2),
            end_date=date(2024, 6, 2),
            attendance=1_000,
            distance_km=1.0,
            true_uplift=0.1,
            venue="Muzeum Narodowe",
        ),
    ]
    assert event_uplift_by_date(events, date(2024, 6, 1)) == pytest.approx(0.2)
    assert event_uplift_by_date(events, date(2024, 6, 2)) == pytest.approx(0.3)
    assert event_uplift_by_date(events, date(2024, 6, 3)) == pytest.approx(0.0)


def test_night_demands_and_bookings_deterministic(tiny_config: DatagenConfig) -> None:
    def run_once():
        rng = seed_rng(tiny_config.seed)
        calendar = build_calendar_frame(tiny_config.horizon, tiny_config.demand)
        events = generate_events(tiny_config, rng)
        nights = build_night_demands(tiny_config, calendar, events, rng)
        bookings = simulate_bookings(tiny_config, nights, rng)
        return nights, bookings

    n1, b1 = run_once()
    n2, b2 = run_once()
    assert [x.demand_latent for x in n1] == [x.demand_latent for x in n2]
    assert b1["booking_id"].tolist() == b2["booking_id"].tolist()
    assert b1["cancelled"].tolist() == b2["cancelled"].tolist()


def test_bookings_respect_capacity(tiny_config: DatagenConfig) -> None:
    rng = seed_rng(tiny_config.seed)
    calendar = build_calendar_frame(tiny_config.horizon, tiny_config.demand)
    events = generate_events(tiny_config, rng)
    nights = build_night_demands(tiny_config, calendar, events, rng)
    bookings = simulate_bookings(tiny_config, nights, rng)

    rooms = {rt.code: rt.rooms for rt in tiny_config.hotel.room_types}
    active = bookings.loc[~bookings["cancelled"]]
    occ: dict[tuple[date, str], int] = {}
    for row in active.itertuples(index=False):
        check_in = pd.Timestamp(row.check_in).date()
        for i in range(int(row.nights)):
            day = date.fromordinal(check_in.toordinal() + i)
            key = (day, str(row.room_type))
            occ[key] = occ.get(key, 0) + 1
            assert occ[key] <= rooms[str(row.room_type)]


def test_cancellation_rate_near_config(tiny_config: DatagenConfig) -> None:
    rng = seed_rng(tiny_config.seed)
    calendar = build_calendar_frame(tiny_config.horizon, tiny_config.demand)
    events = generate_events(tiny_config, rng)
    nights = build_night_demands(tiny_config, calendar, events, rng)
    bookings = simulate_bookings(tiny_config, nights, rng)
    assert len(bookings) > 0
    rate = float(bookings["cancelled"].mean())
    # Tiny horizon → noisy; allow a wide band around 8%.
    assert 0.0 <= rate <= 0.35


def test_cli_writes_nights_and_bookings(tmp_path: Path, tiny_config: DatagenConfig) -> None:
    output = tmp_path / "run"
    assert main(["run", "--config", str(CONFIGS / "tiny.yaml"), "--output", str(output)]) == 0
    nights = pd.read_parquet(output / "nights.parquet")
    bookings = pd.read_parquet(output / "bookings.parquet")
    n_days = (tiny_config.horizon.end - tiny_config.horizon.start).days + 1
    n_types = len(tiny_config.hotel.room_types)
    assert len(nights) == n_days * n_types
    assert nights["demand_latent"].gt(0).all()
    assert nights["optimal_price"].isna().all()
    assert len(bookings) > 0
    assert set(bookings.columns) >= {
        "booking_id",
        "room_type",
        "check_in",
        "check_out",
        "booked_at",
        "nights",
        "price_total",
        "cancelled",
    }
