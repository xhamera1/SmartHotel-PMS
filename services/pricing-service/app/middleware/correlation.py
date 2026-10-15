"""Correlation ID middleware (X-Request-ID), mirroring pms-core."""

from __future__ import annotations

import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

HEADER = "X-Request-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        incoming = request.headers.get(HEADER)
        request_id = incoming.strip() if incoming and incoming.strip() else str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[HEADER] = request_id
        return response
