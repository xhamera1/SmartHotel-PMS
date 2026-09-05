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

See the [implementation plan](../../docs/detailed_implementation_plan.md), §3.2 and Phases 4–7.
