"""Explanation factors attached to each quote response item."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

DEFAULT_TOP_SIGNALS: tuple[str, ...] = (
    "demand_indicator",
    "occupancy_rate",
    "is_weekend",
)


def build_factors(
    *,
    demand_indicator: int,
    occupancy_rate: float,
    is_weekend: bool,
    top_signals: Sequence[str] | None = None,
    major_event_threshold: int = 70,
) -> dict[str, Any]:
    """Human-readable explanation payload persisted by the PMS rate calendar."""

    indicator = int(demand_indicator)
    if indicator < 0 or indicator > 100:
        raise ValueError("demand_indicator must be in [0, 100]")
    if occupancy_rate < 0.0 or occupancy_rate > 1.0:
        raise ValueError("occupancy_rate must be in [0, 1]")

    signals = list(top_signals) if top_signals is not None else list(DEFAULT_TOP_SIGNALS)
    return {
        "demandIndicator": indicator,
        "majorEvent": indicator >= major_event_threshold,
        "weekend": bool(is_weekend),
        "occupancyRate": float(occupancy_rate),
        "topSignals": signals,
    }
