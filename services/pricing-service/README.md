# pricing-service

Dynamic pricing microservice — Python 3.12 · FastAPI · scikit-learn · uv.

Serves price recommendations from a versioned Random Forest model and produces the
event-derived demand indicators that feed it. Owns the `pricing` PostgreSQL schema
via Alembic. Internal-only API (`X-Internal-Api-Key`), consumed by `pms-core`.

| Package | Responsibility | Built in |
|---------|----------------|----------|
| `app/` | FastAPI: routers, schemas, middleware, settings, lifespan | Phase 6 |
| `domain/` | Clamp/round, explanation factors, batch feature frames | Phase 6 |
| `ml/` | Feature engineering, training pipeline, evaluation, model registry | Phase 5 |
| `events/` | Event providers (Ticketmaster/static), Gemini client, scoring | Phase 7 |
| `datagen/` | Synthetic dataset generator (CLI) | Phase 4 |
| `fixtures/` | Committed tiny model for API tests / compose | Phase 6 |
| `tests/` | pytest: domain, API (httpx), integration (testcontainers), ML | Phases 4–6 |
| `migrations/` | Alembic migrations for the `pricing` schema | Phase 1 |

## Run locally

```bash
uv sync
uv run alembic upgrade head     # or: task db-migrate:pricing
task run:pricing                # http://localhost:8081/docs
```

Compose (`app` profile) builds this service with healthcheck on `/health/ready` and
loads the committed fixture model when no active registry row exists
(`ALLOW_FIXTURE_MODEL=true`).

## OpenAPI (D19)

```bash
task openapi:pricing   # writes docs/api/pricing-openapi.json
```

CI regenerates the file and fails on drift. Schemathesis fuzzes `/api/v1/quotes`.

## Event Intelligence (Phase 7)

The `events/` package ingests nearby events and scores their hotel-demand impact.

| Component | Description |
|-----------|-------------|
| `events/providers/` | `EventProvider` ABC with `TicketmasterProvider` (Discovery API v2) and `StaticFileEventProvider` |
| `events/scoring/` | `GeminiScorer` (structured output, circuit breaker) + `HeuristicScorer` (category × distance formula) |
| `events/aggregation.py` | Per-night demand indicator: `min(100, max_score + 0.3 × Σ others × proximity_weight)` |
| `events/sync.py` | `SyncPipeline` orchestrator: fetch → upsert → stale → score → aggregate |
| `events/quota.py` | `DailyCallBudget` for Gemini free-tier discipline |
| `prompts/` | Versioned system prompts with whitelist-based injection defense |

```bash
# Run event sync (static provider, no API keys needed)
task events:sync

# Run with Ticketmaster + Gemini
EVENT_PROVIDER=ticketmaster TICKETMASTER_API_KEY=... GEMINI_API_KEY=... task events:sync

# Live smoke tests (real APIs)
uv run pytest tests/events/test_live_smoke.py -m external
```

Key settings (`HOTEL_LAT`, `HOTEL_LON`, `EVENT_RADIUS_KM`, `EVENT_HORIZON_DAYS`,
`EVENT_PROVIDER`, `GEMINI_MODEL`, `GEMINI_DAILY_CALL_BUDGET`).

## Tests

```bash
task test:python                          # unit + API (no Docker, no external)
uv run pytest -q -m integration           # needs Docker
uv run pytest -q -m benchmark             # 366-item latency (informational)
uv run pytest -q -m external              # live Ticketmaster + Gemini smoke
```

ERD: `docs/diagrams/erd-pricing.md`. Contract: `docs/api/pricing-api.md`.
