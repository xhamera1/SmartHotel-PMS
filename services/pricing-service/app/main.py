"""FastAPI application factory and lifespan."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import sqlalchemy as sa
from fastapi import FastAPI
from sqlalchemy.engine import Engine

from app.errors import register_exception_handlers
from app.middleware.auth import InternalApiKeyMiddleware
from app.middleware.correlation import CorrelationIdMiddleware
from app.routers import demand, events, health, internal, model, quotes
from app.scheduler import start_scheduler, stop_scheduler
from app.services.model_loader import ModelHolder, ModelState, load_active_model
from app.settings import DEFAULT_FIXTURE_MODEL, Settings, get_settings


def create_app(
    settings: Settings | None = None,
    *,
    engine: Engine | None = None,
    initial_model: ModelState | None = None,
) -> FastAPI:
    """Build the ASGI app.

    Tests may inject ``engine`` / ``initial_model`` to avoid a live Postgres
    connection during lifespan startup.
    """

    cfg = settings or get_settings()
    owns_engine = engine is None
    holder = ModelHolder()
    if initial_model is not None:
        holder.set(initial_model)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        settings_local: Settings = app.state.settings
        active_engine = engine or sa.create_engine(
            settings_local.pricing_database_url,
            pool_pre_ping=True,
        )
        app.state.engine = active_engine
        app.state.model_holder = holder
        if initial_model is None:
            try:
                state = load_active_model(
                    active_engine,
                    fixture_dir=DEFAULT_FIXTURE_MODEL,
                    allow_fixture=settings_local.allow_fixture_model,
                )
                holder.set(state)
            except Exception:
                # DB may be down at startup; ready stays false until reload succeeds.
                holder.set(None)
        start_scheduler(active_engine, settings_local)
        yield
        stop_scheduler()
        if owns_engine:
            active_engine.dispose()

    app = FastAPI(
        title="SmartHotel Pricing Service API",
        version="0.1.0",
        description=(
            "Internal pricing microservice. Error contract: RFC 7807 "
            "`application/problem+json` (https://smarthotel/problems/…)."
        ),
        lifespan=lifespan,
    )
    # Eager defaults so httpx ASGITransport (no lifespan) and TestClient both work.
    app.state.settings = cfg
    app.state.engine = engine
    app.state.model_holder = holder
    app.add_middleware(InternalApiKeyMiddleware, api_key=cfg.internal_api_key)
    app.add_middleware(CorrelationIdMiddleware)
    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(quotes.router)
    app.include_router(demand.router)
    app.include_router(events.router)
    app.include_router(model.router)
    app.include_router(internal.router)
    return app


app = create_app()
