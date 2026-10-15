# ml

Machine-learning pipeline for Phase 5.

## Implemented: steps 1–8 + exit-criteria QA

### Shared feature contract

`features.py` is the only place that defines model input names, dtypes, and order.
It exports:

- `FEATURE_SCHEMA` and its canonical SHA-256 `FEATURE_SCHEMA_HASH`;
- derived feature groups and the target contract (`price_multiplier`, `float64`);
- Polish calendar feature construction;
- validated row and DataFrame builders used by datagen, training, and (later) serving.

Datagen snapshot metadata persists both the schema payload and hash. Model artifacts
persist the same hash; serving will reject mismatches in Phase 6 (D20).

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
night remain together.

### Untouched temporal holdout

`splitting.py` reserves the final six months before tuning. For the default
2023-01-01…2025-12-31 dataset this means:

- train: `stay_date <= 2025-06-30` (about 2.5 years),
- test: `stay_date >= 2025-07-01` (the final six months).

Only the train partition enters `RandomizedSearchCV`; final model metrics come from
the untouched test partition.

### Offline evaluation and RQ1 baselines

`evaluation.py` evaluates the frozen model on the untouched holdout and writes:

- `metrics.json`: MAE, RMSE, R², and MAPE (%) for multiplier and resulting PLN price;
- the same metrics by month, event/normal night, and room type;
- RF-versus-baseline MAE improvements and `rf_beats_all_baselines`;
- raw-feature permutation importance using holdout negative MAE;
- batch predict latency for 366 rows (budget ≪ 150 ms);
- `predicted_vs_actual.png`, `residual_distribution.png`,
  `permutation_feature_importance.png`, and `learning_curve.png`.

| ID | Baseline |
|----|----------|
| B0 | Static multiplier `1.0` (base price) |
| B1 | Pre-declared weekday × month multipliers; no target fitting |
| B2 | `LinearRegression` on the same transformed features |

### RQ2 event-feature ablation

`python -m ml.ablation` runs the same protocol twice (with/without event features) and
writes comparison tables under `artifacts/experiments/event-ablation/`.

### Versioned artifacts and registry

`python -m ml.train` writes `artifacts/models/<version>/model.joblib` and
`metadata.json`. Registry CLI:

```shell
python -m ml.registry register --metadata ../../artifacts/models/<version>/metadata.json
python -m ml.registry promote --version <version>
```

### CI metric regression gate

`python -m ml.gate` compares quick-training MAEs to committed `baseline_metrics.json`
(10% tolerance). CI regenerates the default dataset, runs the gate, and uploads evidence.

Root shortcuts: `task ml:train`, `task ml:ablation`, `task ml:promote VERSION=…`,
`task ml:gate`.

### Behavioral / metamorphic QA

`tests/ml/test_metamorphic.py` runs MR1–MR4 against a fitted RF (occupancy ↑, demand ↑,
lead time ↓ under high occupancy, batch permutation invariance). Determinism and
snapshot information-set leakage are covered in `tests/ml/test_determinism.py`.
