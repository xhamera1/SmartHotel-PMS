"""Daily Gemini call budget counter (free-tier quota discipline)."""

from __future__ import annotations

import logging
from datetime import date

logger = logging.getLogger(__name__)


class DailyCallBudget:
    """In-memory counter for daily Gemini API calls."""

    def __init__(self, daily_limit: int = 200) -> None:
        self._limit = daily_limit
        self._today: date | None = None
        self._count = 0

    def _reset_if_new_day(self) -> None:
        today = date.today()
        if self._today != today:
            self._today = today
            self._count = 0

    def can_call(self) -> bool:
        """Return True if budget allows another call."""
        self._reset_if_new_day()
        return self._count < self._limit

    def record_call(self) -> None:
        """Record one API call."""
        self._reset_if_new_day()
        self._count += 1

    @property
    def remaining(self) -> int:
        self._reset_if_new_day()
        return max(0, self._limit - self._count)

    @property
    def count(self) -> int:
        self._reset_if_new_day()
        return self._count
