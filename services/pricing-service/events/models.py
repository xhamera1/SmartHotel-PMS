"""Normalized domain models shared across the events pipeline."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Literal


@dataclass(frozen=True)
class NormalizedEvent:
    """Provider-agnostic event representation, ready for DB upsert."""

    provider: str
    external_id: str
    name: str
    category: str | None
    venue_name: str | None
    city: str | None
    latitude: float | None
    longitude: float | None
    distance_km: float | None
    starts_at: datetime
    ends_at: datetime | None
    expected_attendance: int | None
    url: str | None
    raw_payload: dict[str, Any]

    @property
    def content_hash(self) -> str:
        """SHA-256 over the fields that matter for rescoring decisions."""
        canonical = json.dumps(
            {
                "name": self.name,
                "category": self.category,
                "starts_at": self.starts_at.isoformat(),
                "ends_at": self.ends_at.isoformat() if self.ends_at else None,
                "expected_attendance": self.expected_attendance,
                "distance_km": round(self.distance_km, 2) if self.distance_km is not None else None,
            },
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()


ConfidenceLevel = Literal["LOW", "MEDIUM", "HIGH"]


@dataclass(frozen=True)
class EventScoreResult:
    """One scored event — output of either the Gemini or heuristic scorer."""

    event_external_id: str
    impact_score: int
    confidence: ConfidenceLevel
    affected_nights: list[date] = field(default_factory=list)
    rationale: str = ""
    is_fallback: bool = False
    response_raw: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "impact_score", max(0, min(100, self.impact_score)))
