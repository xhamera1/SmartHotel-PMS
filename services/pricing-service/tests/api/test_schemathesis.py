"""Schemathesis fuzzing against the live OpenAPI contract."""

from __future__ import annotations

import pytest

schemathesis = pytest.importorskip("schemathesis")


def test_openapi_contains_phase6_paths(app) -> None:
    schema = schemathesis.openapi.from_asgi("/openapi.json", app)
    paths = set(schema.raw_schema.get("paths", {}))
    expected = {
        "/api/v1/quotes",
        "/api/v1/demand-indicators",
        "/api/v1/events",
        "/api/v1/model",
        "/internal/model/reload",
        "/internal/events/sync",
        "/health/live",
        "/health/ready",
    }
    assert expected <= paths


def test_schemathesis_quotes_no_server_error(app, auth_headers) -> None:
    """Property fuzz: schema-driven bodies must not 500 (422/401/200 OK)."""
    schema = schemathesis.openapi.from_asgi("/openapi.json", app)
    operation = schema["/api/v1/quotes"]["POST"]
    strategy = operation.as_strategy()
    from hypothesis import HealthCheck, given, settings

    @given(case=strategy)
    @settings(
        max_examples=12,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    )
    def _run(case) -> None:
        headers = dict(getattr(case, "headers", None) or {})
        headers.update(auth_headers)
        response = case.call(headers=headers)
        assert response.status_code < 500

    _run()
