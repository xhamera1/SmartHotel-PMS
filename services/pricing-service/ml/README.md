# ml

Machine-learning pipeline for Phase 5.

## Implemented: steps 1–8

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

### Offline evaluation and RQ1 baselines

`evaluation.py` evaluates the frozen model on the untouched holdout and writes:

- `metrics.json`: MAE, RMSE, R², and MAPE (%) for multiplier and resulting PLN price;
- the same metrics by month, event/normal night, and room type;
- RF-versus-baseline MAE improvements and `rf_beats_all_baselines`;
- raw-feature permutation importance using holdout negative MAE;
- `predicted_vs_actual.png`, `residual_distribution.png`, and
  `permutation_feature_importance.png`.

All compared models use exactly the same temporal holdout:

| ID | Baseline |
|----|----------|
| B0 | Static multiplier `1.0` (base price) |
| B1 | Pre-declared weekday multiplier × monthly season multiplier; no target fitting |
| B2 | `LinearRegression` with the same one-hot/passthrough preprocessing and features |

The manual B1 tables are constants in `baselines.py` and are persisted in
`metrics.json`, so the result is reproducible and cannot be tuned after seeing the
holdout. The RF justification flag is true only when RF has lower overall MAE than
every baseline for both multiplier and PLN price. A failed criterion is reported,
not hidden by aborting artifact generation.

### RQ2 event-feature ablation

`python -m ml.ablation` runs the same temporal split, expanding-window search,
hyperparameter space, random seed, and evaluation twice. The second run removes only
`demand_indicator`, `event_count_active`, and `max_event_score` from the shared
preprocessor. Each run gets its own `metrics.json` and figures. JSON, CSV, and Markdown
comparison tables are generated under `artifacts/experiments/event-ablation/`; no
thesis values need to be copied by hand.

### Versioned artifacts and registry

`python -m ml.train` writes `artifacts/models/<version>/model.joblib` and
`metadata.json`. The sidecar contains the exact dataset SHA-256, training configuration,
selected hyperparameters, model feature list, complete metrics, feature schema and hash,
Git SHA, and UTC training time. Supplying `--register-database-url` also inserts an
inactive row into `pricing.model_registry`.

Registry operations are separate from training:

```shell
python -m ml.registry register --metadata ../../artifacts/models/<version>/metadata.json
python -m ml.registry promote --version <version>
```

The database URL comes from `--database-url` or `PRICING_DATABASE_URL`. Promotion is one
transaction: it locks the requested row, deactivates the previous model, and activates
the requested version. The existing partial unique index guarantees that at most one row
is active.

### CI metric regression gate

`python -m ml.gate` performs deterministic quick training and compares multiplier MAE
and PLN-price MAE with committed `ml/baseline_metrics.json`. A metric may regress by at
most 10%. The command writes `quick_metrics.json` and `gate_report.json`, and returns a
non-zero status on schema mismatch or metric regression. CI regenerates the seeded
default dataset before invoking the gate and uploads both evidence files.

Root shortcuts are available as `task ml:train`, `task ml:ablation`,
`task ml:promote VERSION=<version>`, and `task ml:gate`.

## Remaining Phase 5 work

Behavioral and metamorphic model tests are implemented in the following step.
