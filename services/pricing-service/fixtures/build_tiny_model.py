"""Train and write the committed tiny model fixture used by API tests."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import joblib
import pandas as pd

from ml.features import (
    FEATURE_NAMES,
    FEATURE_SCHEMA_HASH,
    TARGET_NAME,
    build_feature_frame,
    build_feature_row,
)
from ml.pipeline import build_random_forest_pipeline

OUT_DIR = Path(__file__).resolve().parent / "models" / "tiny"


def _snapshots(days: int = 90) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    start = date(2024, 1, 1)
    for offset in range(days):
        stay = start + timedelta(days=offset)
        for room_type, base in (("STD", 250.0), ("DLX", 420.0)):
            occ = (offset % 10) / 10
            demand = offset % 101
            lead = [30, 14, 7, 1][offset % 4]
            feature = build_feature_row(
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
                    **feature,
                    TARGET_NAME: 1.0
                    + 0.35 * occ
                    + 0.002 * demand
                    + (0.05 if room_type == "DLX" else 0.0),
                }
            )
    frame = pd.DataFrame(rows)
    features = build_feature_frame(frame[list(FEATURE_NAMES)].to_dict(orient="records"))
    return pd.concat(
        [
            frame[["stay_date"]].reset_index(drop=True),
            features.reset_index(drop=True),
            frame[[TARGET_NAME]].reset_index(drop=True),
        ],
        axis="columns",
    )


def main() -> None:
    data = _snapshots()
    X = data[list(FEATURE_NAMES)]
    y = data[TARGET_NAME]
    pipeline = build_random_forest_pipeline(random_state=42, n_jobs=1).set_params(
        regressor__n_estimators=40,
        regressor__max_depth=10,
        regressor__min_samples_leaf=2,
        regressor__max_features=1.0,
    )
    pipeline.fit(X, y)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    model_path = OUT_DIR / "model.joblib"
    joblib.dump(pipeline, model_path)
    metadata = {
        "version": "fixture-tiny-v1",
        "algorithm": "RandomForestRegressor",
        "feature_schema_hash": FEATURE_SCHEMA_HASH,
        "dataset_hash": "fixture",
        "artifact_path": str(model_path.as_posix()),
        "trained_at": datetime.now(UTC).isoformat(),
        "config": {"n_estimators": 40, "max_depth": 10, "random_state": 42},
        "metrics": {
            "note": "Committed fixture for API tests; not a holdout evaluation",
            "permutation_importance": [
                {"feature": "demand_indicator", "importance_mean": 0.3},
                {"feature": "occupancy_rate", "importance_mean": 0.2},
                {"feature": "is_weekend", "importance_mean": 0.1},
            ],
        },
        "git_sha": "fixture",
    }
    (OUT_DIR / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(model_path)


if __name__ == "__main__":
    main()
