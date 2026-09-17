# Synthetic dataset generator (Phase 4)

Config-driven CLI that validates Appendix C YAML (Pydantic), seeds RNGs from a single
global `seed`, writes parquet tables plus JSON metadata, and enforces **pandera** data
contracts on every emit. EDA figures via `datagen eda` / notebook.

## Status

| Step | Content | Status |
|------|---------|--------|
| 1 | Config + CLI + empty typed parquet + metadata | **done** |
| 2 | Calendar factors | **done** |
| 3 | Synthetic event catalog | **done** |
| 4 | Demand & booking simulation | **done** |
| 5 | Optimal-price target | **done** |
| 6 | Training snapshots | **done** |
| 7 | EDA + pandera | **done** |

## Usage

From `services/pricing-service`:

```bash
uv sync
uv run python -m datagen run \
  --config datagen/configs/default.yaml \
  --output ../../artifacts/datasets/default

uv run python -m datagen eda \
  --config datagen/configs/default.yaml \
  --input ../../artifacts/datasets/default \
  --figures ../../artifacts/eda/default
```

Tiny fixture:

```bash
task datagen:tiny
```

Or from the repo root: `task datagen` then `task datagen:eda`.

Interactive notebook: `notebooks/eda_datagen.ipynb`.

Dataset specification: [`docs/qa/dataset-spec.md`](../../../docs/qa/dataset-spec.md).

## Outputs

| File | Role |
|------|------|
| `calendar.parquet` | Nightly season / weekday / holiday / bridge factors |
| `events.parquet` | Synthetic events + true uplift |
| `nights.parquet` | Per (date, room type) demand / optimal price |
| `bookings.parquet` | Simulated bookings |
| `snapshots.parquet` | Lead-time rows following the canonical `ml/features.py` contract |
| `validation_report.json` | Pandera pass/fail per table |
| `metadata.json` | Config + feature-schema hashes, seed, row counts, validation status |

Default snapshot size ≈ 3 × 365 × 3 × 5 ≈ **16 440** rows. Generation fails loudly if any
pandera contract is violated.
