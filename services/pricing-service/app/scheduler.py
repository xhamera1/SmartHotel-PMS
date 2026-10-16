"""APScheduler daily event sync job (Phase 7, plan §6 Phase 7 step 2)."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.engine import Engine

from app.settings import Settings

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _run_event_sync(engine: Engine, settings: Settings) -> None:
    """Execute the full event sync pipeline as a scheduled job."""
    from events.sync import run_sync

    try:
        result = await run_sync(engine, settings)
        logger.info("Scheduled event sync completed: %s", result)
    except Exception:
        logger.exception("Scheduled event sync failed")


def start_scheduler(engine: Engine, settings: Settings) -> AsyncIOScheduler | None:
    """Start the APScheduler if event sync scheduling is enabled.

    Returns the scheduler instance (for shutdown) or None if disabled.
    """
    global _scheduler

    if not settings.event_sync_schedule_enabled:
        logger.info("Event sync scheduler disabled (EVENT_SYNC_SCHEDULE_ENABLED=false)")
        return None

    scheduler = AsyncIOScheduler(timezone="Europe/Warsaw")
    trigger = CronTrigger(
        hour=settings.event_sync_hour,
        minute=settings.event_sync_minute,
        timezone="Europe/Warsaw",
    )
    scheduler.add_job(
        _run_event_sync,
        trigger=trigger,
        args=[engine, settings],
        id="daily_event_sync",
        name="Daily event sync (Ticketmaster → Gemini scoring → daily_demand)",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "Event sync scheduler started — daily at %02d:%02d Europe/Warsaw",
        settings.event_sync_hour,
        settings.event_sync_minute,
    )
    return scheduler


def stop_scheduler() -> None:
    """Shut down the scheduler if running."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Event sync scheduler stopped")
