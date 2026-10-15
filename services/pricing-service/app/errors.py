"""RFC 7807 application/problem+json error contract (mirrors PMS)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_TYPE_BASE = "https://smarthotel/problems"


def problem_response(
    *,
    status_code: int,
    title: str,
    detail: str,
    type_suffix: str,
    request_id: str | None = None,
    errors: list[dict[str, Any]] | None = None,
    instance: str | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": f"{PROBLEM_TYPE_BASE}/{type_suffix}",
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    if instance is not None:
        body["instance"] = instance
    if request_id is not None:
        body["requestId"] = request_id
    if errors is not None:
        body["errors"] = errors
    return JSONResponse(
        status_code=status_code,
        content=body,
        media_type="application/problem+json",
    )


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {
                "loc": [str(part) for part in err.get("loc", ())],
                "msg": err.get("msg", "invalid"),
                "type": err.get("type", "value_error"),
            }
            for err in exc.errors()
        ]
        return problem_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            title="Validation Error",
            detail="Request validation failed",
            type_suffix="validation-error",
            request_id=_request_id(request),
            errors=errors,
            instance=str(request.url.path),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        suffix = {
            401: "unauthorized",
            403: "forbidden",
            404: "not-found",
            503: "service-unavailable",
        }.get(exc.status_code, "http-error")
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return problem_response(
            status_code=exc.status_code,
            title=detail if exc.status_code < 500 else "Internal Server Error",
            detail=detail,
            type_suffix=suffix,
            request_id=_request_id(request),
            instance=str(request.url.path),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        return problem_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Internal Server Error",
            detail="An unexpected error occurred",
            type_suffix="internal-error",
            request_id=_request_id(request),
            instance=str(request.url.path),
        )
