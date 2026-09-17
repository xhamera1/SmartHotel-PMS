# ml

Machine-learning pipeline for Phase 5.

## Implemented: steps 1–3

### Shared feature contract

`features.py` is the only place that defines model input names, dtypes, and order.
It exports:

- `FEATURE_SCHEMA` and its canonical SHA-256 `FEATURE_SCHEMA_HASH`;
- derived feature groups and the target contract (`price_multiplier`, `float64`);
- Polish calendar feature construction;
- validated row and DataFrame builders used by datagen now and training/serving later.

Datagen snapshot metadata persists both the schema payload and hash. Model artifacts
will persist the same hash in Phase 5 step 7, and serving will reject mismatches in
Phase 6 (D20).

Calendar ordinals (`day_of_week`, `month`, ISO `week_of_year`) intentionally have no
cyclic encoding: tree ensembles can split ordinal inputs directly. This design choice
and the discontinuity at calendar boundaries must be stated as a model limitation in
the thesis.

### Random Forest pipeline and tuning

`pipeline.py` builds one sklearn `Pipeline`:

1. `ColumnTransformer`: `OneHotEncoder(handle_unknown="ignore")` for `room_type`,
   passthrough for all numeric/boolean features from the shared schema;
2. `RandomForestRegressor` with fixed `random_state` and pinned `n_jobs`;
3. deterministic `RandomizedSearchCV`, scored with validation MAE, over
   `n_estimators=200..600`, `max_depth=8..24`, `min_samples_leaf=1..20`, and
   configured `max_features` candidates.

The search receives `ExpandingWindowSplit`, never random K-fold. CV operates on
unique `stay_date` groups, so all room types and lead-time snapshots for one hotel
night remain together. Each successive training window contains all previous
training dates and validation is always later in time.

### Untouched temporal holdout

`splitting.py` reserves the final six months before tuning. For the default
2023-01-01…2025-12-31 dataset this means:

- train: `stay_date <= 2025-06-30` (about 2.5 years),
- test: `stay_date >= 2025-07-01` (the final six months).

Only the train partition enters `RandomizedSearchCV`; the selected estimator is
refitted on the full train partition. CV scores are tuning diagnostics. Final model
metrics must be computed once from the returned untouched test partition in Step 4.

## Remaining Phase 5 work

Offline metrics and plots, baselines, event-feature ablation, artifact registry,
regression gate, and behavioral tests are implemented in the following steps.
