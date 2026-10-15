"""Prompt builder: whitelist-based, injection-safe event serialization."""

from __future__ import annotations

from pathlib import Path

from events.models import NormalizedEvent

PROMPT_DIR = Path(__file__).resolve().parents[2] / "prompts"

EVENT_DELIMITER_START = "<<<EVENT>>>"
EVENT_DELIMITER_END = "<<<END_EVENT>>>"
MAX_NAME_LENGTH = 300

WHITELIST_FIELDS = (
    "name",
    "category",
    "venue_name",
    "city",
    "distance_km",
    "starts_at",
    "ends_at",
    "expected_attendance",
)


def load_system_prompt(version: str = "event-impact-v1") -> str:
    """Read the versioned system prompt from the prompts/ directory."""
    # Try hyphenated name first, then underscored (filesystem convention).
    for filename in (f"{version}.md", f"{version.replace('-', '_')}.md"):
        path = PROMPT_DIR / filename
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
    raise FileNotFoundError(f"Prompt template not found for version: {version}")


def _sanitize_name(name: str) -> str:
    """Length-cap and strip control characters from event names."""
    clean = name.replace("\n", " ").replace("\r", " ").strip()
    return clean[:MAX_NAME_LENGTH]


def serialize_event(event: NormalizedEvent) -> str:
    """Serialize one event using only whitelisted fields with delimiters."""
    lines = [EVENT_DELIMITER_START]
    lines.append(f"name: {_sanitize_name(event.name)}")
    lines.append(f"category: {event.category or 'UNKNOWN'}")
    lines.append(f"venue_name: {event.venue_name or 'N/A'}")
    lines.append(f"city: {event.city or 'N/A'}")
    lines.append(f"distance_km: {event.distance_km if event.distance_km is not None else 'N/A'}")
    lines.append(f"starts_at: {event.starts_at.isoformat()}")
    lines.append(f"ends_at: {event.ends_at.isoformat() if event.ends_at else 'N/A'}")
    lines.append(
        f"expected_attendance: {event.expected_attendance if event.expected_attendance else 'N/A'}"
    )
    lines.append(EVENT_DELIMITER_END)
    return "\n".join(lines)


def build_user_prompt(events: list[NormalizedEvent]) -> str:
    """Build the user-message content with all events delimited."""
    if not events:
        return "No events to score."
    blocks = [serialize_event(e) for e in events]
    header = f"Score the following {len(events)} event(s):\n"
    return header + "\n\n".join(blocks)
