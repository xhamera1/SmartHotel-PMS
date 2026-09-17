# Synthetic dataset generator (Phase 4)

Config-driven CLI that validates Appendix C YAML (Pydantic), seeds RNGs from a single
global `seed`, and writes parquet tables plus a JSON metadata sidecar under
`artifacts/datasets/` (git-ignored).

## Status

| Step | Content | Status |
|------|---------|--------|
| 1 | Config + CLI + empty typed parquet + metadata | **done** |
| 2 | Calendar factors | pending |
| 3 | Synthetic event catalog | pending |
| 4 | Demand & booking simulation | pending |
| 5 | Optimal-price target | pending |
| 6 | Training snapshots | pending |
| 7 | EDA + pandera | pending |

## Usage

From `services/pricing-service`:

```bash
uv sync
uv run python -m datagen run \
  --config datagen/configs/default.yaml \
  --output ../../artifacts/datasets/default
```

Tiny fixture config (for tests / later golden hashes):

```bash
uv run python -m datagen run \
  --config datagen/configs/tiny.yaml \
  --output ../../artifacts/datasets/tiny
```

Or from the repo root: `task datagen`.

## Outputs

| File | Role |
|------|------|
| `events.parquet` | Synthetic events + true uplift (step 3) |
| `nights.parquet` | Per (date, room type) demand / optimal price (steps 4–5) |
| `bookings.parquet` | Simulated bookings (step 4) |
| `snapshots.parquet` | Lead-time training rows (step 6) |
| `metadata.json` | `config_hash`, `seed`, `row_counts`, file map |

Step 1 writes **empty typed frames** so the IO contract is exercised before simulation lands.
