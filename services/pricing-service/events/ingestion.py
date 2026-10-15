"""Event ingestion: upsert, content_hash, stale marking."""

from __future__ import annotations

import json
import logging
from typing import Any

import sqlalchemy as sa

from events.models import NormalizedEvent

logger = logging.getLogger(__name__)


def upsert_events(engine: sa.Engine, events: list[NormalizedEvent]) -> list[dict[str, Any]]:
    """
    Upsert normalized events into ``pricing.events``.

    Returns a list of dicts ``{"id": ..., "external_id": ..., "is_new_or_changed": bool}``
    indicating which events need (re)scoring.
    """
    if not events:
        return []

    results: list[dict[str, Any]] = []
    upsert_sql = sa.text(
        """
        INSERT INTO pricing.events (
            provider, external_id, name, category, venue_name, city,
            latitude, longitude, distance_km,
            starts_at, ends_at, expected_attendance, url,
            raw_payload, content_hash, status
        ) VALUES (
            :provider, :external_id, :name, :category, :venue_name, :city,
            :latitude, :longitude, :distance_km,
            :starts_at, :ends_at, :expected_attendance, :url,
            CAST(:raw_payload AS jsonb), :content_hash, 'NEW'
        )
        ON CONFLICT (provider, external_id) DO UPDATE SET
            name = EXCLUDED.name,
            category = EXCLUDED.category,
            venue_name = EXCLUDED.venue_name,
            city = EXCLUDED.city,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            distance_km = EXCLUDED.distance_km,
            starts_at = EXCLUDED.starts_at,
            ends_at = EXCLUDED.ends_at,
            expected_attendance = EXCLUDED.expected_attendance,
            url = EXCLUDED.url,
            raw_payload = EXCLUDED.raw_payload,
            content_hash = EXCLUDED.content_hash,
            fetched_at = now(),
            status = CASE
                WHEN pricing.events.content_hash != EXCLUDED.content_hash THEN 'NEW'
                ELSE pricing.events.status
            END
        RETURNING id, external_id,
            (xmax = 0) AS is_insert,
            CASE WHEN xmax = 0 THEN true
                 WHEN content_hash != :old_hash THEN true
                 ELSE false
            END AS is_new_or_changed
        """
    )

    with engine.begin() as conn:
        for event in events:
            old_hash_row = conn.execute(
                sa.text(
                    "SELECT content_hash FROM pricing.events "
                    "WHERE provider = :p AND external_id = :eid"
                ),
                {"p": event.provider, "eid": event.external_id},
            ).first()
            old_hash = old_hash_row[0] if old_hash_row else ""

            row = (
                conn.execute(
                    upsert_sql,
                    {
                        "provider": event.provider,
                        "external_id": event.external_id,
                        "name": event.name,
                        "category": event.category,
                        "venue_name": event.venue_name,
                        "city": event.city,
                        "latitude": event.latitude,
                        "longitude": event.longitude,
                        "distance_km": event.distance_km,
                        "starts_at": event.starts_at,
                        "ends_at": event.ends_at,
                        "expected_attendance": event.expected_attendance,
                        "url": event.url,
                        "raw_payload": json.dumps(event.raw_payload, default=str),
                        "content_hash": event.content_hash,
                        "old_hash": old_hash,
                    },
                )
                .mappings()
                .first()
            )
            if row:
                results.append(dict(row))

    new_count = sum(1 for r in results if r.get("is_new_or_changed"))
    logger.info("Upserted %d events (%d new/changed)", len(results), new_count)
    return results


def mark_stale(engine: sa.Engine) -> int:
    """Mark events whose end date has passed as STALE. Returns count."""
    with engine.begin() as conn:
        result = conn.execute(
            sa.text(
                """
                UPDATE pricing.events
                SET status = 'STALE'
                WHERE status != 'STALE'
                  AND (
                    (ends_at IS NOT NULL AND ends_at < now())
                    OR (ends_at IS NULL AND starts_at < now() - interval '1 day')
                  )
                """
            )
        )
        count = result.rowcount
    if count:
        logger.info("Marked %d events as STALE", count)
    return count


def insert_scores(
    engine: sa.Engine,
    event_db_id: int,
    score: dict[str, Any],
    *,
    llm_model: str | None = None,
    prompt_version: str | None = None,
) -> None:
    """Insert one event_scores row."""
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                """
                INSERT INTO pricing.event_scores (
                    event_id, impact_score, confidence, affected_nights,
                    rationale, llm_model, prompt_version, response_raw, is_fallback
                ) VALUES (
                    :event_id, :impact_score, :confidence, :affected_nights,
                    :rationale, :llm_model, :prompt_version,
                    CAST(:response_raw AS jsonb), :is_fallback
                )
                """
            ),
            {
                "event_id": event_db_id,
                "impact_score": score["impact_score"],
                "confidence": _confidence_to_numeric(score.get("confidence", "MEDIUM")),
                "affected_nights": score.get("affected_nights", []),
                "rationale": score.get("rationale", ""),
                "llm_model": llm_model,
                "prompt_version": prompt_version,
                "response_raw": json.dumps(score.get("response_raw") or {}, default=str),
                "is_fallback": score.get("is_fallback", False),
            },
        )
        conn.execute(
            sa.text("UPDATE pricing.events SET status = 'SCORED' WHERE id = :eid"),
            {"eid": event_db_id},
        )


def _confidence_to_numeric(confidence: str) -> float:
    return {"LOW": 0.3, "MEDIUM": 0.6, "HIGH": 0.9}.get(confidence.upper(), 0.5)


def get_event_db_id(engine: sa.Engine, provider: str, external_id: str) -> int | None:
    """Look up the DB id for a (provider, external_id) pair."""
    with engine.connect() as conn:
        row = conn.execute(
            sa.text("SELECT id FROM pricing.events WHERE provider = :p AND external_id = :eid"),
            {"p": provider, "eid": external_id},
        ).first()
    return int(row[0]) if row else None


def events_needing_scoring(
    engine: sa.Engine,
    *,
    prompt_version: str,
    llm_model: str,
) -> list[dict[str, Any]]:
    """Return events that are NEW or whose latest score used a different prompt/model."""
    with engine.connect() as conn:
        rows = conn.execute(
            sa.text(
                """
                SELECT e.id, e.provider, e.external_id, e.name, e.category,
                       e.venue_name, e.city, e.latitude, e.longitude, e.distance_km,
                       e.starts_at, e.ends_at, e.expected_attendance, e.url,
                       e.content_hash
                FROM pricing.events e
                WHERE e.status IN ('NEW', 'SCORED')
                  AND NOT EXISTS (
                      SELECT 1 FROM pricing.event_scores es
                      WHERE es.event_id = e.id
                        AND es.prompt_version = :pv
                        AND es.llm_model = :model
                  )
                ORDER BY e.starts_at
                """
            ),
            {"pv": prompt_version, "model": llm_model},
        ).mappings()
        return [dict(r) for r in rows]
