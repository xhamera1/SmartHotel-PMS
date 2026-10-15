"""Abstract base for event scorers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from events.models import EventScoreResult, NormalizedEvent


class EventScorer(ABC):
    """Port: score a batch of normalized events."""

    @abstractmethod
    async def score(self, events: list[NormalizedEvent]) -> list[EventScoreResult]:
        """Return one score result per input event."""
