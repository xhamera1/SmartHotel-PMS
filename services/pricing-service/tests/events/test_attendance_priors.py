"""Attendance prior helpers for Ticketmaster gaps."""

from events.attendance_priors import estimate_attendance


def test_known_capacity_not_overridden() -> None:
    value, assumed = estimate_attendance(
        category="MUSIC",
        expected_attendance=22000,
        venue_name="Tauron Arena Kraków",
    )
    assert value == 22000
    assert assumed is False


def test_tauron_venue_prior() -> None:
    value, assumed = estimate_attendance(
        category="MUSIC",
        venue_name="Tauron Arena Kraków",
        event_name="KoRn",
    )
    assert value == 18000
    assert assumed is True


def test_category_fallback_when_venue_unknown() -> None:
    value, assumed = estimate_attendance(category="SPORTS", venue_name="Unknown Hall")
    assert value == 10000
    assert assumed is True
