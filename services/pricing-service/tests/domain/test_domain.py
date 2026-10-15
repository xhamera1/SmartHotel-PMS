"""Unit tests for domain clamp/round, factors, and batch feature frames."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from domain.factors import build_factors
from domain.features_batch import DemandSnapshot, QuoteFeatureInput, build_feature_frame_from_batch
from domain.pricing import clamp_and_round
from ml.features import FEATURE_NAMES


def test_clamp_and_round_half_up_to_whole_pln() -> None:
    price, multiplier = clamp_and_round(
        base_price=250.0,
        multiplier=1.234,
        min_price=180.0,
        max_price=450.0,
    )
    assert price == Decimal("309")
    assert multiplier == pytest.approx(309.0 / 250.0)


def test_clamp_respects_max_guardrail() -> None:
    price, _ = clamp_and_round(
        base_price=250.0,
        multiplier=3.0,
        min_price=180.0,
        max_price=450.0,
    )
    assert price == Decimal("450")


def test_clamp_respects_min_guardrail() -> None:
    price, _ = clamp_and_round(
        base_price=250.0,
        multiplier=0.5,
        min_price=180.0,
        max_price=450.0,
    )
    assert price == Decimal("180")


def test_clamp_rejects_inverted_band() -> None:
    with pytest.raises(ValueError, match="min_price"):
        clamp_and_round(
            base_price=250.0,
            multiplier=1.0,
            min_price=500.0,
            max_price=450.0,
        )


def test_build_factors_flags() -> None:
    factors = build_factors(
        demand_indicator=78,
        occupancy_rate=0.83,
        is_weekend=True,
        top_signals=["demand_indicator", "occupancy_rate"],
    )
    assert factors["majorEvent"] is True
    assert factors["weekend"] is True
    assert factors["demandIndicator"] == 78
    assert factors["topSignals"] == ["demand_indicator", "occupancy_rate"]


def test_build_factors_no_major_event_below_threshold() -> None:
    factors = build_factors(demand_indicator=20, occupancy_rate=0.4, is_weekend=False)
    assert factors["majorEvent"] is False
    assert factors["weekend"] is False


def test_batch_feature_frame_column_wise_and_demand_join() -> None:
    items = [
        QuoteFeatureInput(
            stay_date=date(2024, 6, 15),
            room_type="STD",
            base_price=250.0,
            occupancy_rate=0.5,
            rooms_remaining=5,
            lead_time_days=14,
        ),
        QuoteFeatureInput(
            stay_date=date(2024, 6, 16),
            room_type="DLX",
            base_price=420.0,
            occupancy_rate=0.8,
            rooms_remaining=2,
            lead_time_days=7,
        ),
    ]
    demand = {
        date(2024, 6, 15): DemandSnapshot(indicator=40, event_count_active=1, max_event_score=40),
    }
    frame = build_feature_frame_from_batch(items, demand)
    assert list(frame.columns) == list(FEATURE_NAMES)
    assert len(frame) == 2
    assert int(frame.loc[0, "demand_indicator"]) == 40
    assert int(frame.loc[1, "demand_indicator"]) == 0  # missing night → zero
    assert str(frame.loc[0, "room_type"]) == "STD"
    assert int(frame.loc[1, "lead_time_days"]) == 7
