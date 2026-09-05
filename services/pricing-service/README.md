# pricing-service

Dynamic pricing microservice — Python 3.12 · FastAPI · scikit-learn · uv.

Serves price recommendations from a versioned Random Forest model and produces the
event-derived demand indicators that feed it. Owns the `pricing` PostgreSQL schema
via Alembic. Internal-only API (`X-Internal-Api-Key`), consumed by `pms-core`.

| Package | Responsibility | Built in |
|---------|----------------|----------|
| `app/` | API layer: routers, schemas, middleware, settings | Phase 6 |
| `domain/` | Pricing domain logic: clamping, rounding, factors | Phase 6 |
| `ml/` | Feature engineering, training pipeline, evaluation, model registry | Phase 5 |
| `events/` | Event providers (Ticketmaster/static), Gemini client, scoring, aggregation | Phase 7 |
| `datagen/` | Synthetic dataset generator (CLI) | Phase 4 |
| `tests/` | pytest suite: unit, integration (Testcontainers), contract | Phases 4–7 |
| `migrations/` | Alembic migrations for the `pricing` schema (**present**) | Phase 1 |

Database migrations (URL from `PRICING_DATABASE_URL`, see `.env.example`):

```bash
uv run alembic upgrade head     # or from the repo root: task db-migrate:pricing
```

ERD: `docs/diagrams/erd-pricing.md`. See ADR-0003 for the service-topology rationale.
