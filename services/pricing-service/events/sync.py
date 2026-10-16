"""Sync pipeline orchestrator — ingestion, scoring, aggregation."""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime
from typing import Any

import sqlalchemy as sa

from app.settings import Settings
from events.aggregation import aggregate_demand, upsert_daily_demand
from events.ingestion import (
    events_needing_scoring,
    get_event_db_id,
    insert_scores,
    mark_stale,
    upsert_events,
)
from events.models import NormalizedEvent
from events.providers.base import EventProvider
from events.providers.static import StaticFileEventProvider
from events.providers.ticketmaster import TicketmasterProvider
from events.quota import DailyCallBudget
from events.scoring.base import EventScorer
from events.scoring.heuristic import HeuristicScorer

logger = logging.getLogger(__name__)


def _build_provider(settings: Settings) -> EventProvider:
    provider_type = settings.event_provider.lower()
    if provider_type == "ticketmaster":
        if not settings.ticketmaster_api_key:
            raise ValueError("TICKETMASTER_API_KEY is required for ticketmaster provider")
        return TicketmasterProvider(
            api_key=settings.ticketmaster_api_key,
            hotel_lat=settings.hotel_lat,
            hotel_lon=settings.hotel_lon,
            radius_km=settings.event_radius_km,
            horizon_days=settings.event_horizon_days,
        )
    return StaticFileEventProvider()


def _build_scorers(settings: Settings, budget: DailyCallBudget) -> list[EventScorer]:
    """Return scorers in priority order: Gemini first (if configured), then heuristic."""
    scorers: list[EventScorer] = []
    if settings.gemini_api_key:
        from events.scoring.gemini import GeminiScorer

        scorers.append(
            GeminiScorer(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
                prompt_version=settings.prompt_version,
                budget_check=budget.can_call,
            )
        )
    scorers.append(HeuristicScorer())
    return scorers


class SyncPipeline:
    """Orchestrate: fetch → upsert → score → aggregate."""

    def __init__(self, engine: sa.Engine, settings: Settings) -> None:
        self._engine = engine
        self._settings = settings
        self._budget = DailyCallBudget(settings.gemini_daily_call_budget)

    async def run(self) -> dict[str, Any]:
        """Execute the full sync pipeline. Returns a summary dict."""
        summary: dict[str, Any] = {"started_at": datetime.now().isoformat()}

        # 1. Fetch
        provider = _build_provider(self._settings)
        events = await provider.fetch_events()
        summary["events_fetched"] = len(events)

        if not events:
            summary["status"] = "no_events"
            return summary

        # 2. Upsert + stale
        upsert_results = upsert_events(self._engine, events)
        stale_count = mark_stale(self._engine)
        summary["events_upserted"] = len(upsert_results)
        summary["events_stale"] = stale_count

        # 3. Score new/changed events — skip those already scored with
        # the current prompt_version + llm_model (LLM response cache, D9)
        events_by_eid = {e.external_id: e for e in events}
        to_score: list[NormalizedEvent] = []
        to_score_db_ids: dict[str, int] = {}

        # Determine which events actually need scoring (cache check)
        primary_model = self._settings.gemini_model if self._settings.gemini_api_key else "heuristic"
        already_scored_eids: set[str] = set()
        try:
            needing = events_needing_scoring(
                self._engine,
                prompt_version=self._settings.prompt_version,
                llm_model=primary_model,
            )
            needing_eids = {r["external_id"] for r in needing}
        except Exception:
            logger.warning("Cache check query failed — scoring all new/changed events")
            needing_eids = None

        for result in upsert_results:
            eid = result["external_id"]
            if not result.get("is_new_or_changed"):
                continue
            if eid not in events_by_eid:
                continue
            # Skip if already scored with matching prompt+model (cache hit)
            if needing_eids is not None and eid not in needing_eids:
                already_scored_eids.add(eid)
                continue
            to_score.append(events_by_eid[eid])
            to_score_db_ids[eid] = result["id"]

        summary["events_to_score"] = len(to_score)
        summary["events_cache_hit"] = len(already_scored_eids)

        if to_score:
            scorers = _build_scorers(self._settings, self._budget)
            score_results = await self._score_events(to_score, scorers)

            for score_result in score_results:
                db_id = to_score_db_ids.get(score_result.event_external_id)
                if db_id is None:
                    db_id = get_event_db_id(self._engine, "static", score_result.event_external_id)
                if db_id is not None:
                    insert_scores(
                        self._engine,
                        db_id,
                        {
                            "impact_score": score_result.impact_score,
                            "confidence": score_result.confidence,
                            "affected_nights": [
                                d.isoformat() for d in score_result.affected_nights
                            ],
                            "rationale": score_result.rationale,
                            "is_fallback": score_result.is_fallback,
                            "response_raw": score_result.response_raw,
                        },
                        llm_model=(
                            self._settings.gemini_model
                            if not score_result.is_fallback
                            else "heuristic"
                        ),
                        prompt_version=self._settings.prompt_version,
                    )
                    self._budget.record_call()

            summary["events_scored"] = len(score_results)
            summary["fallback_count"] = sum(1 for s in score_results if s.is_fallback)

        # 4. Aggregate
        scored_for_agg = self._load_scored_events_for_aggregation()
        demand = aggregate_demand(scored_for_agg)
        nights_updated = upsert_daily_demand(self._engine, demand)
        summary["nights_updated"] = nights_updated
        summary["status"] = "completed"
        summary["budget_remaining"] = self._budget.remaining

        return summary

    async def _score_events(
        self, events: list[NormalizedEvent], scorers: list[EventScorer]
    ) -> list:
        """Try scorers in priority order; fall back on failure."""
        from events.models import EventScoreResult

        results: list[EventScoreResult] = []
        remaining = list(events)

        for scorer in scorers:
            if not remaining:
                break
            try:
                scored = await scorer.score(remaining)
                scored_ids = {s.event_external_id for s in scored}
                results.extend(scored)
                remaining = [e for e in remaining if e.external_id not in scored_ids]
            except Exception:
                logger.exception("Scorer %s failed", type(scorer).__name__)
                continue

        return results

    def _load_scored_events_for_aggregation(self) -> list[dict]:
        """Load all non-stale scored events with their latest score for aggregation."""
        with self._engine.connect() as conn:
            rows = conn.execute(
                sa.text(
                    """
                    SELECT e.id AS event_db_id,
                           e.distance_km,
                           es.impact_score,
                           es.affected_nights
                    FROM pricing.events e
                    JOIN LATERAL (
                        SELECT impact_score, affected_nights
                        FROM pricing.event_scores sc
                        WHERE sc.event_id = e.id
                        ORDER BY sc.scored_at DESC
                        LIMIT 1
                    ) es ON true
                    WHERE e.status = 'SCORED'
                    """
                )
            ).mappings()
            return [dict(r) for r in rows]


async def run_sync(engine: sa.Engine, settings: Settings) -> dict[str, Any]:
    """Convenience async entry point."""
    pipeline = SyncPipeline(engine, settings)
    return await pipeline.run()


def main() -> int:
    """CLI entry point: ``python -m events.sync``."""
    from app.settings import get_settings

    settings = get_settings()
    engine = sa.create_engine(settings.pricing_database_url, pool_pre_ping=True)
    try:
        result = asyncio.run(run_sync(engine, settings))
        print(f"Sync completed: {result}")  # noqa: T201
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
