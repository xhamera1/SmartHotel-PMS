"""Abstract base for event providers (D8)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from events.models import NormalizedEvent


class EventProvider(ABC):
    """Port: fetch normalized events from an external source."""

    @abstractmethod
    async def fetch_events(self) -> list[NormalizedEvent]:
        """Return all events within the configured horizon."""
