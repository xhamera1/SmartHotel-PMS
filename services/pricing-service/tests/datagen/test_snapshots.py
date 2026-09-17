"""Tests for lead-time training snapshots (Phase 4 step 6)."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest

from datagen.calendar import build_calendar_frame
from datagen.cli import main
from datagen.config import DatagenConfig
from datagen.demand import build_night_demands, nights_to_frame, simulate_bookings
from datagen.events import generate_events
from datagen.pipeline import seed_rng
from datagen.snapshots import (
    booking_claims_by_night,
    build_snapshots,
    occupancy_as_of,
)

CONFIGS = Path(__file__).resolve().parents[2] / "datagen" / "configs"


@pytest.fixture
def tiny_config() -> DatagenConfig:
    return DatagenConfig.from_yaml(CONFIGS / "tiny.yaml")


def _run_through_bookings(config: DatagenConfig):
    rng = seed_rng(config.seed)
    calendar = build_calendar_frame(config.horizon, config.demand)
    events = generate_events(config, rng)
    nights = build_night_demands(config, calendar, events, rng)
    nights_df = nights_to_frame(nights, room_types=config.hotel.room_types)
    bookings = simulate_bookings(config, nights, rng)
    return calendar, events, nights_df, bookings


def test_occupancy_ignores_future_bookings() -> None:
    """Information-set rule: only bookings with booked_at ≤ snapshot_date count."""
    stay = date(2024, 6, 10)
    room = "STD"
    bookings = pd.DataFrame(
        {
            "booking_id": ["B1", "B2", "B3"],
            "room_type": [room, room, room],
            "check_in": [stay, stay, stay],
            "check_out": [stay + timedelta(days=1)] * 3,
            "booked_at": [
                stay - timedelta(days=20),
                stay - timedelta(days=5),
                stay - timedelta(days=2),  # after snapshot at L=7
            ],
            "nights": [1, 1, 1],
            "price_total": [250.0, 250.0, 250.0],
            "cancelled": [False, False, False],
        }
    )
    claims = booking_claims_by_night(bookings)
    snapshot = stay - timedelta(days=7)
    occ, remaining = occupancy_as_of(
        claims,
        stay_date=stay,
        room_type=room,
        snapshot_date=snapshot,
        rooms=5,
    )
    # snapshot = stay−7: B1 (stay−20) counts; B2 (stay−5) and B3 (stay−2) are future.
    assert occ == pytest.approx(1 / 5)
    assert remaining == 4


def test_cancelled_bookings_do_not_occupy() -> None:
    stay = date(2024, 6, 10)
    bookings = pd.DataFrame(
        {
            "booking_id": ["B1"],
            "room_type": ["STD"],
            "check_in": [stay],
            "check_out": [stay + timedelta(days=1)],
            "booked_at": [stay - timedelta(days=30)],
            "nights": [1],
            "price_total": [250.0],
            "cancelled": [True],
        }
    )
    claims = booking_claims_by_night(bookings)
    occ, remaining = occupancy_as_of(
        claims,
        stay_date=stay,
        room_type="STD",
        snapshot_date=stay - timedelta(days=1),
        rooms=5,
    )
    assert occ == 0.0
    assert remaining == 5


def test_snapshot_row_count_and_bounds(tiny_config: DatagenConfig) -> None:
    calendar, events, nights_df, bookings = _run_through_bookings(tiny_config)
    snaps = build_snapshots(tiny_config, calendar, events, nights_df, bookings)

    n_days = (tiny_config.horizon.end - tiny_config.horizon.start).days + 1
    n_types = len(tiny_config.hotel.room_types)
    n_leads = len(tiny_config.snapshots.lead_times_days)
    assert len(snaps) == n_days * n_types * n_leads

    assert snaps["occupancy_so_far"].between(0.0, 1.0).all()
    assert (snaps["rooms_remaining"] >= 0).all()
    assert set(snaps["lead_time_days"]) == set(tiny_config.snapshots.lead_times_days)

    # snapshot_date = stay_date - lead_time
    derived = (
        pd.to_datetime(snaps["stay_date"]) - pd.to_timedelta(snaps["lead_time_days"], unit="D")
    )
    assert (derived == pd.to_datetime(snaps["snapshot_date"])).all()


def test_snapshot_target_matches_nights(tiny_config: DatagenConfig) -> None:
    calendar, events, nights_df, bookings = _run_through_bookings(tiny_config)
    snaps = build_snapshots(tiny_config, calendar, events, nights_df, bookings)

    night_m = nights_df.set_index(["date", "room_type"])["price_multiplier"]
    for row in snaps.itertuples(index=False):
        key = (pd.Timestamp(row.stay_date), row.room_type)
        assert float(row.price_multiplier) == pytest.approx(float(night_m.loc[key]))


def test_later_lead_time_occupancy_not_lower(tiny_config: DatagenConfig) -> None:
    """Closer to stay (smaller lead), occupancy_so_far is non-decreasing."""
    calendar, events, nights_df, bookings = _run_through_bookings(tiny_config)
    snaps = build_snapshots(tiny_config, calendar, events, nights_df, bookings)

    leads = sorted(tiny_config.snapshots.lead_times_days, reverse=True)  # far → near
    for (_, _), group in snaps.groupby(["stay_date", "room_type"], sort=False):
        ordered = group.set_index("lead_time_days").loc[leads]
        occ = ordered["occupancy_so_far"].tolist()
        assert occ == sorted(occ)  # non-decreasing as lead shrinks (far→near in leads)


def test_snapshots_deterministic(tiny_config: DatagenConfig) -> None:
    a = _run_through_bookings(tiny_config)
    b = _run_through_bookings(tiny_config)
    s1 = build_snapshots(tiny_config, *a)
    s2 = build_snapshots(tiny_config, *b)
    pd.testing.assert_frame_equal(s1, s2)


def test_cli_writes_snapshots(tmp_path: Path, tiny_config: DatagenConfig) -> None:
    output = tmp_path / "run"
    assert main(["run", "--config", str(CONFIGS / "tiny.yaml"), "--output", str(output)]) == 0
    snaps = pd.read_parquet(output / "snapshots.parquet")
    n_days = (tiny_config.horizon.end - tiny_config.horizon.start).days + 1
    expected = n_days * len(tiny_config.hotel.room_types) * len(
        tiny_config.snapshots.lead_times_days
    )
    assert len(snaps) == expected
    assert set(snaps.columns) >= set(
        {
            "stay_date",
            "room_type",
            "snapshot_date",
            "lead_time_days",
            "occupancy_so_far",
            "rooms_remaining",
            "season_factor",
            "weekday_factor",
            "holiday_flag",
            "event_uplift_known",
            "price_multiplier",
        }
    )
