"""Lead-time training snapshots with information-set features (Phase 4 step 6)."""

from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict
from datetime import date, timedelta

import pandas as pd

from datagen.config import DatagenConfig
from datagen.demand import event_uplift_by_date
from datagen.events import SyntheticEvent
from datagen.tables import SNAPSHOTS_COLUMNS, empty_frame


def _as_date(value: object) -> date:
    if isinstance(value, date) and not isinstance(value, pd.Timestamp):
        return value
    return pd.Timestamp(value).date()  # type: ignore[arg-type]


def booking_claims_by_night(
    bookings: pd.DataFrame,
) -> dict[tuple[date, str], list[date]]:
    """
    Map (stay_night, room_type) → sorted ``booked_at`` dates for *active* inventory.

    Cancelled bookings never hold rooms (sim cancels at booking time). Each stay night
    covered by a booking contributes one claim timed at ``booked_at``.
    """
    claims: dict[tuple[date, str], list[date]] = defaultdict(list)
    if bookings.empty:
        return claims

    active = bookings.loc[~bookings["cancelled"]]
    for row in active.itertuples(index=False):
        check_in = _as_date(row.check_in)
        stay_nights = int(row.nights)
        room_type = str(row.room_type)
        booked_at = _as_date(row.booked_at)
        for i in range(stay_nights):
            stay_night = check_in + timedelta(days=i)
            claims[(stay_night, room_type)].append(booked_at)

    for key in claims:
        claims[key].sort()
    return claims


def occupancy_as_of(
    claims: dict[tuple[date, str], list[date]],
    *,
    stay_date: date,
    room_type: str,
    snapshot_date: date,
    rooms: int,
) -> tuple[float, int]:
    """
    Occupancy knowable on ``snapshot_date`` for ``stay_date`` / ``room_type``.

    Counts only claims with ``booked_at <= snapshot_date`` (no future booking leakage).
    Returns ``(occupancy_so_far ∈ [0, 1], rooms_remaining)``.
    """
    if rooms <= 0:
        raise ValueError("rooms must be positive")
    booked_ats = claims.get((stay_date, room_type), [])
    occupied = bisect_right(booked_ats, snapshot_date)
    occupied = min(occupied, rooms)
    remaining = rooms - occupied
    return occupied / rooms, remaining


def build_snapshots(
    config: DatagenConfig,
    calendar: pd.DataFrame,
    events: list[SyntheticEvent],
    nights: pd.DataFrame,
    bookings: pd.DataFrame,
) -> pd.DataFrame:
    """
    One row per (stay_date, room_type, lead_time) with features known at that moment.

    Target ``price_multiplier`` is the night-level optimum (D7); it does not vary with
    lead time. Event uplift uses the public event calendar for the stay night (same
    indicator available to serving). Occupancy uses only bookings placed by snapshot.
    """
    if nights.empty:
        return empty_frame(SNAPSHOTS_COLUMNS)

    lead_times = list(config.snapshots.lead_times_days)
    rooms_by_type = {rt.code: rt.rooms for rt in config.hotel.room_types}
    claims = booking_claims_by_night(bookings)

    cal = calendar.copy()
    cal["date_key"] = pd.to_datetime(cal["date"]).dt.date
    cal_by_date = {
        row.date_key: row
        for row in cal.itertuples(index=False)
    }

    # Event uplift is a stay-night calendar feature (announced publicly).
    uplift_cache: dict[date, float] = {}

    rows: list[dict[str, object]] = []
    for night in nights.itertuples(index=False):
        stay_date = _as_date(night.date)
        room_type = str(night.room_type)
        rooms = rooms_by_type[room_type]
        cal_row = cal_by_date.get(stay_date)
        if cal_row is None:
            msg = f"calendar missing stay_date {stay_date}"
            raise KeyError(msg)

        if stay_date not in uplift_cache:
            uplift_cache[stay_date] = event_uplift_by_date(events, stay_date)
        event_known = uplift_cache[stay_date]
        multiplier = float(night.price_multiplier)

        for lead in lead_times:
            snapshot_date = stay_date - timedelta(days=lead)
            occ, remaining = occupancy_as_of(
                claims,
                stay_date=stay_date,
                room_type=room_type,
                snapshot_date=snapshot_date,
                rooms=rooms,
            )
            rows.append(
                {
                    "stay_date": stay_date,
                    "room_type": room_type,
                    "snapshot_date": snapshot_date,
                    "lead_time_days": lead,
                    "occupancy_so_far": occ,
                    "rooms_remaining": remaining,
                    "season_factor": float(cal_row.season_factor),
                    "weekday_factor": float(cal_row.weekday_factor),
                    "holiday_flag": int(cal_row.holiday_flag),
                    "event_uplift_known": event_known,
                    "price_multiplier": multiplier,
                }
            )

    frame = pd.DataFrame(rows)
    frame["stay_date"] = pd.to_datetime(frame["stay_date"])
    frame["snapshot_date"] = pd.to_datetime(frame["snapshot_date"])
    frame["lead_time_days"] = frame["lead_time_days"].astype("int64")
    frame["rooms_remaining"] = frame["rooms_remaining"].astype("int64")
    frame["holiday_flag"] = frame["holiday_flag"].astype("int64")
    return frame
