"""Database helpers for demand, events, prediction_log, readiness."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

import sqlalchemy as sa

from domain.features_batch import DemandSnapshot


def check_db(engine: sa.Engine | None) -> bool:
    if engine is None:
        return False
    try:
        with engine.connect() as connection:
            connection.execute(sa.text("SELECT 1"))
        return True
    except Exception:
        return False


def fetch_demand_by_dates(engine: sa.Engine, dates: set[date]) -> dict[date, DemandSnapshot]:
    if not dates:
        return {}
    with engine.connect() as connection:
        rows = connection.execute(
            sa.text(
                """
                SELECT date, indicator
                FROM pricing.daily_demand
                WHERE date = ANY(:dates)
                """
            ),
            {"dates": list(dates)},
        ).mappings()
        result: dict[date, DemandSnapshot] = {}
        for row in rows:
            day = row["date"]
            if hasattr(day, "isoformat"):
                day = date.fromisoformat(day.isoformat())
            indicator = int(row["indicator"])
            result[day] = DemandSnapshot(
                indicator=indicator,
                event_count_active=1 if indicator > 0 else 0,
                max_event_score=indicator,
            )
        return result


def fetch_demand_range(engine: sa.Engine, start: date, end: date) -> list[dict[str, Any]]:
    with engine.connect() as connection:
        rows = connection.execute(
            sa.text(
                """
                SELECT date, indicator, top_event_ids
                FROM pricing.daily_demand
                WHERE date >= :start AND date <= :end
                ORDER BY date
                """
            ),
            {"start": start, "end": end},
        ).mappings()
        return [dict(row) for row in rows]


def fetch_events_range(engine: sa.Engine, start: date, end: date) -> list[dict[str, Any]]:
    with engine.connect() as connection:
        rows = connection.execute(
            sa.text(
                """
                SELECT e.id, e.name, e.category, e.starts_at, e.ends_at, e.distance_km,
                       s.impact_score
                FROM pricing.events e
                LEFT JOIN LATERAL (
                    SELECT impact_score
                    FROM pricing.event_scores es
                    WHERE es.event_id = e.id
                    ORDER BY es.scored_at DESC
                    LIMIT 1
                ) s ON true
                WHERE e.starts_at::date <= :end
                  AND COALESCE(e.ends_at::date, e.starts_at::date) >= :start
                ORDER BY e.starts_at
                """
            ),
            {"start": start, "end": end},
        ).mappings()
        return [dict(row) for row in rows]


def insert_prediction_logs(
    engine: sa.Engine,
    rows: list[dict[str, Any]],
) -> None:
    if not rows:
        return
    statement = sa.text(
        """
        INSERT INTO pricing.prediction_log (
            request_id, room_type_code, stay_date, features, multiplier, price, model_version
        ) VALUES (
            :request_id, :room_type_code, :stay_date, CAST(:features AS jsonb),
            :multiplier, :price, :model_version
        )
        """
    )
    with engine.begin() as connection:
        for row in rows:
            connection.execute(
                statement,
                {
                    **row,
                    "features": __import__("json").dumps(row["features"]),
                    "multiplier": float(row["multiplier"]),
                    "price": float(Decimal(row["price"])),
                },
            )
