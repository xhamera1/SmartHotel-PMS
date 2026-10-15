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

## Tests

```bash
task test:python                          # unit + API (no Docker)
uv run pytest -q -m integration           # needs Docker
uv run pytest -q -m benchmark             # 366-item latency (informational)
```

ERD: `docs/diagrams/erd-pricing.md`. Contract: `docs/api/pricing-api.md`.
