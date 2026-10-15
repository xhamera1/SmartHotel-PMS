"""Column-wise batch feature-frame construction for quote serving."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

import pandas as pd

from ml.features import FEATURE_NAMES, build_feature_frame, calendar_features


@dataclass(frozen=True)
class QuoteFeatureInput:
    """One quote item stripped to fields needed for the model frame."""

    stay_date: date
    room_type: str
    base_price: float
    occupancy_rate: float
    rooms_remaining: int
    lead_time_days: int


@dataclass(frozen=True)
class DemandSnapshot:
    """Nightly demand features joined from ``pricing.daily_demand`` (+ scores)."""

    indicator: int = 0
    event_count_active: int = 0
    max_event_score: int = 0


def build_feature_frame_from_batch(
    items: Sequence[QuoteFeatureInput],
    demand_by_date: Mapping[date, DemandSnapshot] | None = None,
) -> pd.DataFrame:
    """
    Build the shared model feature frame for a whole quote batch.

    Columns are assembled as lists (vectorized), then passed through
    ``ml.features.build_feature_frame``. Never uses per-row ``DataFrame.apply``.
    Missing demand rows default to zeros.
    """
    if not items:
        return build_feature_frame([])

    demand = demand_by_date or {}
    columns: dict[str, list[object]] = {name: [] for name in FEATURE_NAMES}

    for item in items:
        cal = calendar_features(item.stay_date)
        snap = demand.get(item.stay_date, DemandSnapshot())
        values: dict[str, object] = {
            **cal,
            "lead_time_days": int(item.lead_time_days),
            "occupancy_rate": float(item.occupancy_rate),
            "rooms_remaining": int(item.rooms_remaining),
            "base_price": float(item.base_price),
            "room_type": str(item.room_type).strip(),
            "demand_indicator": int(snap.indicator),
            "event_count_active": int(snap.event_count_active),
            "max_event_score": int(snap.max_event_score),
        }
        for name in FEATURE_NAMES:
            columns[name].append(values[name])

    rows = [{name: columns[name][index] for name in FEATURE_NAMES} for index in range(len(items))]
    return build_feature_frame(rows)
