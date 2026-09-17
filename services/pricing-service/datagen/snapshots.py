"""Lead-time training snapshots with information-set features (Phase 4 step 6)."""

from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict
from datetime import date, timedelta

import pandas as pd

from datagen.config import DatagenConfig
from datagen.events import SyntheticEvent
from datagen.tables import SNAPSHOTS_COLUMNS, empty_frame
from ml.features import FEATURE_NAMES, TARGET_NAME, build_feature_frame, build_feature_row


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


def _event_features_by_date(
    events: list[SyntheticEvent],
) -> dict[date, tuple[int, int, int]]:
    """Return synthetic equivalents of the future scored-event pipeline.

    Datagen's ground-truth uplift is mapped deterministically onto the same 0..100
    impact-score scale that Phase 7 will estimate from real event data. This bridge is
    synthetic-data-only; serving will receive scored events. The nightly demand
    indicator follows D9: max score plus 30% of the remaining active-event scores,
    capped at 100.
    """

    scores_by_date: dict[date, list[int]] = defaultdict(list)
    for event in events:
        score = min(100, max(0, round(event.true_uplift * 100)))
        active_date = event.start_date
        while active_date <= event.end_date:
            scores_by_date[active_date].append(score)
            active_date += timedelta(days=1)

    result: dict[date, tuple[int, int, int]] = {}
    for active_date, scores in scores_by_date.items():
        maximum = max(scores)
        indicator = min(100, round(maximum + 0.3 * (sum(scores) - maximum)))
        result[active_date] = (indicator, len(scores), maximum)
    return result


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
    lead time. Feature values are built by ``ml.features`` so datagen and the future
    serving path share names, order, dtypes, calendar semantics, and validation.
    Occupancy uses only bookings placed by the snapshot date.
    """
    if nights.empty:
        return empty_frame(SNAPSHOTS_COLUMNS)

    lead_times = list(config.snapshots.lead_times_days)
    rooms_by_type = {rt.code: rt.rooms for rt in config.hotel.room_types}
    claims = booking_claims_by_night(bookings)

    cal = calendar.copy()
    cal["date_key"] = pd.to_datetime(cal["date"]).dt.date
    cal_by_date = {row.date_key: row for row in cal.itertuples(index=False)}

    event_features = _event_features_by_date(events)

    rows: list[dict[str, object]] = []
    for night in nights.itertuples(index=False):
        stay_date = _as_date(night.date)
        room_type = str(night.room_type)
        rooms = rooms_by_type[room_type]
        cal_row = cal_by_date.get(stay_date)
        if cal_row is None:
            msg = f"calendar missing stay_date {stay_date}"
            raise KeyError(msg)

        multiplier = float(night.price_multiplier)
        demand_indicator, event_count, max_event_score = event_features.get(stay_date, (0, 0, 0))

        for lead in lead_times:
            snapshot_date = stay_date - timedelta(days=lead)
            occ, remaining = occupancy_as_of(
                claims,
                stay_date=stay_date,
                room_type=room_type,
                snapshot_date=snapshot_date,
                rooms=rooms,
            )
            feature_row = build_feature_row(
                stay_date=stay_date,
                lead_time_days=lead,
                occupancy_rate=occ,
                rooms_remaining=remaining,
                base_price=float(night.base_price),
                room_type=room_type,
                demand_indicator=demand_indicator,
                event_count_active=event_count,
                max_event_score=max_event_score,
            )
            rows.append(
                {
                    "stay_date": stay_date,
                    "snapshot_date": snapshot_date,
                    **feature_row,
                    "price_multiplier": multiplier,
                }
            )

    context = pd.DataFrame(rows)
    features = build_feature_frame(context.loc[:, list(FEATURE_NAMES)].to_dict(orient="records"))
    identifiers = context.loc[:, ["stay_date", "snapshot_date"]].apply(pd.to_datetime)
    target = context.loc[:, [TARGET_NAME]].astype("float64")
    frame = pd.concat([identifiers, features, target], axis="columns")
    return frame.loc[:, list(SNAPSHOTS_COLUMNS)]
