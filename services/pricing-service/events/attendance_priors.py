"""Attendance priors when Ticketmaster omits venue capacity."""

from __future__ import annotations

CATEGORY_DEFAULT_ATTENDANCE: dict[str, int] = {
    "MUSIC": 2500,
    "SPORTS": 10000,
    "CONFERENCE": 2000,
    "CULTURE": 1200,
}
DEFAULT_ATTENDANCE = 1500

# (substring in venue or event name, estimated capacity) — first match wins.
# Ordered specific → generic; Kraków-centric but harmless elsewhere.
VENUE_ATTENDANCE_RULES: list[tuple[str, int]] = [
    ("tauron", 18000),
    ("t-mobile arena", 18000),
    ("stadion miejski", 33000),
    ("stadion wisły", 33000),
    ("stadion cracovii", 15000),
    ("cracovia", 15000),
    ("ice kraków", 8000),
    ("ice congress", 8000),
    ("expo Kraków", 6000),
    ("expo krakow", 6000),
    ("hala widowiskowo", 5000),
    ("auditorium maximum", 1200),
    ("filharmonia", 900),
    ("opera", 800),
    ("teatr", 600),
    ("klub studio", 1500),
    ("kwadrat", 800),
    ("forum", 800),
    ("piwnica", 250),
    ("jazz", 300),
    ("club", 600),
    ("klub", 600),
]


def estimate_attendance(
    *,
    category: str | None,
    expected_attendance: int | None = None,
    venue_name: str | None = None,
    event_name: str | None = None,
) -> tuple[int, bool]:
    """Return (attendance, assumed). Assumed when capacity was not provided by the provider."""
    if expected_attendance is not None and expected_attendance > 0:
        return expected_attendance, False

    haystack = f"{venue_name or ''} {event_name or ''}".lower()
    for needle, capacity in VENUE_ATTENDANCE_RULES:
        if needle in haystack:
            return capacity, True

    cat = (category or "").upper()
    return CATEGORY_DEFAULT_ATTENDANCE.get(cat, DEFAULT_ATTENDANCE), True
