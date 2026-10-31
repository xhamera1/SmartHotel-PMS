"""Correlation ID + HTTP access logging (X-Request-ID / traceId), Phase 10."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

HEADER = "X-Request-ID"

log = structlog.get_logger("app.http")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        incoming = request.headers.get(HEADER)
        request_id = incoming.strip() if incoming and incoming.strip() else str(uuid.uuid4())
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(traceId=request_id, requestId=request_id)

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = int((time.perf_counter() - start) * 1000)
            path = request.url.path
            if not path.startswith("/health"):
                log.info(
                    "http_request",
                    **{
                        "http.method": request.method,
                        "http.path": path,
                        "http.status": 500,
                        "durationMs": duration_ms,
                    },
                )
            structlog.contextvars.clear_contextvars()
            raise

        duration_ms = int((time.perf_counter() - start) * 1000)
        path = request.url.path
        if not path.startswith("/health"):
            log.info(
                "http_request",
                **{
                    "http.method": request.method,
                    "http.path": path,
                    "http.status": response.status_code,
                    "durationMs": duration_ms,
                },
            )
        response.headers[HEADER] = request_id
        structlog.contextvars.clear_contextvars()
        return response
