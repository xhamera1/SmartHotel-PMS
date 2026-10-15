"""Metamorphic relations MR1–MR4 against a fitted Random Forest (Phase 5 QA)."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline

from ml.features import build_feature_frame, build_feature_row
from ml.pipeline import build_random_forest_pipeline

# Soft mono tolerance: RF is not a monotone model; allow tiny numeric/tree jitter.
MONO_TOL = 0.05
ORDER_TOL = 1e-9


def _synthetic_snapshots(days: int = 180) -> tuple[pd.DataFrame, pd.Series]:
    """Synthetic world where occupancy, demand, and short lead raise the target."""

    rows: list[dict[str, object]] = []
    targets: list[float] = []
    start = date(2024, 1, 1)
    rng = np.random.default_rng(42)
    for offset in range(days):
        stay = start + timedelta(days=offset)
        for room_type, base in (("STD", 250.0), ("DLX", 420.0)):
            occ = float(rng.uniform(0.0, 1.0))
            demand = int(rng.integers(0, 101))
            lead = int(rng.choice([1, 7, 14, 30, 60]))
            remaining = max(0, int(round(20 * (1.0 - occ))))
            rows.append(
                build_feature_row(
                    stay_date=stay,
                    lead_time_days=lead,
                    occupancy_rate=occ,
                    rooms_remaining=remaining,
                    base_price=base,
                    room_type=room_type,
                    demand_indicator=demand,
                    event_count_active=1 if demand >= 40 else 0,
                    max_event_score=demand,
                )
            )
            # Ground truth encodes the metamorphic directions we will probe.
            target = (
                1.0
                + 0.45 * occ
                + 0.004 * demand
                + (0.08 if lead <= 7 and occ >= 0.7 else 0.0)
                + (0.05 if room_type == "DLX" else 0.0)
                + float(rng.normal(0.0, 0.02))
            )
            targets.append(max(0.5, target))
    return build_feature_frame(rows), pd.Series(targets, name="price_multiplier")


@pytest.fixture(scope="module")
def fitted_rf() -> Pipeline:
    X, y = _synthetic_snapshots()
    pipeline = build_random_forest_pipeline(random_state=42, n_jobs=1).set_params(
        regressor__n_estimators=80,
        regressor__max_depth=12,
        regressor__min_samples_leaf=2,
        regressor__max_features=1.0,
    )
    pipeline.fit(X, y)
    return pipeline


def _base_row(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "stay_date": date(2024, 6, 15),
        "lead_time_days": 14,
        "occupancy_rate": 0.4,
        "rooms_remaining": 12,
        "base_price": 250.0,
        "room_type": "STD",
        "demand_indicator": 20,
        "event_count_active": 0,
        "max_event_score": 20,
    }
    values.update(overrides)
    return build_feature_row(**values)  # type: ignore[arg-type]


def _predict_one(model: Pipeline, **overrides: object) -> float:
    frame = build_feature_frame([_base_row(**overrides)])
    return float(model.predict(frame)[0])


def test_mr1_higher_occupancy_does_not_decrease_multiplier(fitted_rf: Pipeline) -> None:
    low = _predict_one(fitted_rf, occupancy_rate=0.2, rooms_remaining=16)
    high = _predict_one(fitted_rf, occupancy_rate=0.9, rooms_remaining=2)
    assert high >= low - MONO_TOL


def test_mr2_higher_demand_indicator_does_not_decrease_multiplier(fitted_rf: Pipeline) -> None:
    low = _predict_one(
        fitted_rf,
        demand_indicator=0,
        event_count_active=0,
        max_event_score=0,
    )
    high = _predict_one(
        fitted_rf,
        demand_indicator=90,
        event_count_active=1,
        max_event_score=90,
    )
    assert high >= low - MONO_TOL


def test_mr3_shorter_lead_with_high_occupancy_does_not_decrease(fitted_rf: Pipeline) -> None:
    far = _predict_one(
        fitted_rf,
        occupancy_rate=0.85,
        rooms_remaining=3,
        lead_time_days=60,
    )
    near = _predict_one(
        fitted_rf,
        occupancy_rate=0.85,
        rooms_remaining=3,
        lead_time_days=1,
    )
    assert near >= far - MONO_TOL


def test_mr4_predictions_permutation_invariant(fitted_rf: Pipeline) -> None:
    rows = [
        _base_row(occupancy_rate=0.1 + i * 0.1, rooms_remaining=18 - i, demand_indicator=10 * i)
        for i in range(8)
    ]
    ordered = build_feature_frame(rows)
    perm = np.random.default_rng(7).permutation(len(ordered))
    shuffled = ordered.iloc[perm].reset_index(drop=True)

    pred_ordered = fitted_rf.predict(ordered)
    pred_shuffled = fitted_rf.predict(shuffled)

    recovered = np.empty_like(pred_ordered)
    for shuffled_idx, original_idx in enumerate(perm):
        recovered[original_idx] = pred_shuffled[shuffled_idx]
    np.testing.assert_allclose(pred_ordered, recovered, atol=ORDER_TOL, rtol=0.0)
