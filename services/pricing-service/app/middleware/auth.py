"""Internal API-key auth middleware (constant-time compare)."""

from __future__ import annotations

import hmac
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.errors import PROBLEM_TYPE_BASE

HEADER = "X-Internal-Api-Key"
EXEMPT_PREFIXES = ("/health/", "/docs", "/redoc", "/openapi.json")


class InternalApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, api_key: str) -> None:  # noqa: ANN001
        super().__init__(app)
        self._api_key = api_key.encode("utf-8")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if path == "/" or any(path.startswith(prefix) for prefix in EXEMPT_PREFIXES):
            return await call_next(request)

        provided = request.headers.get(HEADER)
        if provided is None or not hmac.compare_digest(
            provided.encode("utf-8"),
            self._api_key,
        ):
            request_id = getattr(request.state, "request_id", None)
            body = {
                "type": f"{PROBLEM_TYPE_BASE}/unauthorized",
                "title": "Unauthorized",
                "status": 401,
                "detail": "Missing or invalid X-Internal-Api-Key",
                "instance": path,
            }
            if request_id:
                body["requestId"] = request_id
            return JSONResponse(
                status_code=401,
                content=body,
                media_type="application/problem+json",
            )
        return await call_next(request)
