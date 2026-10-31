"""Correlation middleware binds traceId into structlog contextvars."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.correlation import HEADER, CorrelationIdMiddleware


def test_echoes_and_binds_trace_id() -> None:
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)

    @app.get("/ping")
    def ping() -> dict[str, str]:
        import structlog

        ctx = structlog.contextvars.get_contextvars()
        return {"traceId": str(ctx.get("traceId", ""))}

    client = TestClient(app)
    planted = "phase10-corr-abc"
    response = client.get("/ping", headers={HEADER: planted})
    assert response.status_code == 200
    assert response.headers.get(HEADER) == planted
    assert response.json()["traceId"] == planted
