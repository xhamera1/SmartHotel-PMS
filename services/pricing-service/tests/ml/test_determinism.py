"""Determinism and snapshot information-set leakage checks (Phase 5 QA)."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from datagen.calendar import build_calendar_frame
from datagen.config import DatagenConfig
from datagen.demand import build_night_demands, nights_to_frame, simulate_bookings
from datagen.events import generate_events
from datagen.pipeline import seed_rng
from datagen.snapshots import build_snapshots
from ml.evaluation import regression_metrics
from ml.features import FEATURE_NAMES, TARGET_NAME, build_feature_frame, build_feature_row
from ml.pipeline import TrainingConfig, tune_random_forest

CONFIGS = Path(__file__).resolve().parents[2] / "datagen" / "configs"


def _long_snapshots(days: int = 240) -> pd.DataFrame:
    """Enough history for a 6-month holdout and deterministic quick tuning."""

    rows: list[dict[str, object]] = []
    start = date(2024, 1, 1)
    for offset in range(days):
        stay = start + timedelta(days=offset)
        for room_type, base in (("STD", 250.0), ("DLX", 420.0)):
            occ = (offset % 10) / 10
            demand = offset % 101
            lead = [30, 14, 7, 1][offset % 4]
            row = build_feature_row(
                stay_date=stay,
                lead_time_days=lead,
                occupancy_rate=occ,
                rooms_remaining=max(0, 10 - int(occ * 10)),
                base_price=base,
                room_type=room_type,
                demand_indicator=demand,
                event_count_active=1 if demand >= 50 else 0,
                max_event_score=demand,
            )
            rows.append(
                {
                    "stay_date": pd.Timestamp(stay),
                    **row,
                    TARGET_NAME: 1.0
                    + 0.3 * occ
                    + 0.002 * demand
                    + (0.05 if room_type == "DLX" else 0.0),
                }
            )
    frame = pd.DataFrame(rows)
    features = build_feature_frame(frame[list(FEATURE_NAMES)].to_dict(orient="records"))
    out = pd.concat(
        [
            frame[["stay_date"]].reset_index(drop=True),
            features.reset_index(drop=True),
            frame[[TARGET_NAME]].reset_index(drop=True),
        ],
        axis="columns",
    )
    return out


def _quick_metrics(snapshots: pd.DataFrame) -> dict[str, float | None]:
    training = tune_random_forest(
        snapshots,
        config=TrainingConfig(
            holdout_months=6,
            cv_splits=2,
            cv_validation_days=21,
            search_iterations=1,
            random_state=42,
            n_jobs=1,
        ),
        param_distributions={
            "regressor__n_estimators": [10],
            "regressor__max_depth": [8],
            "regressor__min_samples_leaf": [2],
            "regressor__max_features": [1.0],
        },
    )
    predicted = training.best_pipeline.predict(training.split.X_test)
    metrics = regression_metrics(
        training.split.y_test,
        predicted,
        training.split.X_test["base_price"],
    )
    return {
        "multiplier_mae": metrics["multiplier"]["mae"],
        "multiplier_rmse": metrics["multiplier"]["rmse"],
        "multiplier_r2": metrics["multiplier"]["r2"],
        "price_pln_mae": metrics["price_pln"]["mae"],
    }


def test_same_seed_yields_identical_core_metrics() -> None:
    snapshots = _long_snapshots()
    first = _quick_metrics(snapshots)
    second = _quick_metrics(snapshots)
    assert first == second


def test_snapshot_information_set_dates_and_occupancy() -> None:
    """ML-side re-check of Phase 4: snapshot_date and occupancy knowable at that moment."""

    config = DatagenConfig.from_yaml(CONFIGS / "tiny.yaml")
    rng = seed_rng(config.seed)
    calendar = build_calendar_frame(config.horizon, config.demand)
    events = generate_events(config, rng)
    nights = build_night_demands(config, calendar, events, rng)
    nights_df = nights_to_frame(nights, room_types=config.hotel.room_types)
    bookings = simulate_bookings(config, nights, rng)
    snaps = build_snapshots(config, calendar, events, nights_df, bookings)

    derived = pd.to_datetime(snaps["stay_date"]) - pd.to_timedelta(
        snaps["lead_time_days"], unit="D"
    )
    assert (derived == pd.to_datetime(snaps["snapshot_date"])).all()
    assert snaps["occupancy_rate"].between(0.0, 1.0).all()
    assert (snaps["rooms_remaining"] >= 0).all()

    # Closer lead times must not show lower occupancy (no future booking leakage).
    leads = sorted(config.snapshots.lead_times_days, reverse=True)
    for (_, _), group in snaps.groupby(["stay_date", "room_type"], sort=False):
        ordered = group.set_index("lead_time_days").loc[leads]
        occ = ordered["occupancy_rate"].tolist()
        assert occ == sorted(occ)
