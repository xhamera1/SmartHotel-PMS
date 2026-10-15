# app

FastAPI API layer: routers, Pydantic v2 schemas (`extra="forbid"`, camelCase),
correlation-ID + internal API-key middleware, `pydantic-settings`, lifespan model
load with `feature_schema_hash` validation, problem+json errors.

Entry: `uvicorn app.main:app` or `task run:pricing`.
OpenAPI export: `python -m app.export_openapi`.
