# Synthetic dataset specification (Phase 4)

This document is the data contract for SmartHotel’s synthetic generator
(`services/pricing-service/datagen`). Executable checks live in
`datagen/schemas.py` (pandera) and run on every `python -m datagen run`.

## Purpose

Generate a reproducible hotel demand world with a **known** revenue-optimal
price multiplier target (`m* = p*/base_price`, ADR-0010 / D7), plus lead-time
training snapshots for Random Forest. Latent demand shocks
(`latent_shock_sigma`) deliberately keep the mapping from features → target
imperfect (honest R² ceiling).

## Generator

| Item | Value |
|------|--------|
| Entry | `uv run python -m datagen run --config … --output …` |
| Config | Appendix C YAML, Pydantic-validated (`DatagenConfig`) |
| Seed | Single global seed (Python + NumPy) |
| Outputs | Parquet tables + `metadata.json` + `validation_report.json` |
| Default horizon | 2023-01-01 → 2025-12-31 (~3 years) |
| Default snapshots | ~16 440 rows (1096 nights × 3 room types × 5 leads) |

Tiny fixture: `datagen/configs/tiny.yaml` (14 days, 2 room types, leads `[7, 1]`).

## Tables

### `calendar.parquet`

One row per stay night in the horizon.

| Column | Bounds / notes |
|--------|----------------|
| `date` | Unique |
| `season_factor` | `> 0` (sinusoid + December bump) |
| `weekday_factor` | `> 0` (Mon…Sun multipliers) |
| `holiday_flag`, `bridge_flag` | `{0, 1}` (Polish holidays + bridge days) |
| `holiday_factor`, `calendar_factor` | `> 0` |

### `events.parquet`

~60 events/year (configurable). Template names/descriptions feed Phase 13 Gemini E3.

| Column | Bounds / notes |
|--------|----------------|
| `event_id` | Unique |
| `category` | `MUSIC` \| `SPORTS` \| `CONFERENCE` \| `CULTURE` |
| `start_date` ≤ `end_date` | Duration 1–3 days |
| `attendance` | `> 0` |
| `distance_km` | `≥ 0` |
| `true_uplift` | `≥ 0` (hidden ground truth for demand) |

### `nights.parquet`

One row per `(date, room_type)`.

| Column | Bounds / notes |
|--------|----------------|
| `(date, room_type)` | Unique |
| `demand_latent` | `D = rooms·1.35·season·weekday·holiday·(1+event)·exp(ε)` |
| `optimal_price` | Grid-searched `p*` in `[min_price, max_price]` (1 PLN step) |
| `price_multiplier` | `m* = p*/base_price` — **ML target** |

### `bookings.parquet`

Booking-level simulation: Poisson attempts, gamma lead times (~24d mean),
logistic conversion vs WTP, capacity, ~8% cancellations.

| Column | Bounds / notes |
|--------|----------------|
| `booking_id` | Unique |
| `check_out` | `> check_in` |
| `nights` | `≥ 1` |
| `price_total` | `> 0` |
| `cancelled` | bool |

### `snapshots.parquet`

Training rows: one per `(stay_date, room_type, lead_time_days)`.

| Column | Bounds / notes |
|--------|----------------|
| Composite key | Unique |
| `snapshot_date` | `stay_date − lead_time_days` (`< stay_date`) |
| `occupancy_so_far` | `[0, 1]` — only bookings with `booked_at ≤ snapshot_date` |
| `rooms_remaining` | `≥ 0` |
| `event_uplift_known` | Public calendar uplift for the stay night |
| `price_multiplier` | Night-level target (constant across leads) |

**Information-set rule:** snapshot features must be knowable at `snapshot_date`.
Occupancy never includes future bookings (enforced by unit tests).

## Validation

- Pandera schemas: `datagen/schemas.py`
- Runner: `datagen/validate.py` → fails the CLI on contract violation
- Report: `validation_report.json` (`status: passed|failed` + per-table errors)

## EDA

Figures (also produced by `python -m datagen eda`):

1. Seasonal decomposition of `calendar_factor`
2. Occupancy histogram
3. Price–demand scatter (`optimal_price` vs `demand_latent`)
4. Snapshot correlation heatmap
5. Event-uplift time series + uplift vs occupancy

Notebook: `services/pricing-service/notebooks/eda_datagen.ipynb`  
Headless: `task datagen:eda` → `artifacts/eda/default/`

## Design notes for the thesis

1. **Latent noise** (`noise_sigma` + `latent_shock_sigma`) prevents a perfectly
   learnable world — evaluation remains credible.
2. **Multiplier target** generalises across room types; serving clamps
   `base_price × m̂` to `[min_price, max_price]` (ADR-0009 grosz rounding).
3. **Lead-time snapshots** teach booking-curve dynamics without leaking future
   occupancy.
