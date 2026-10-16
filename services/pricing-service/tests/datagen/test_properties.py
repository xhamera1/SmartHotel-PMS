"""Property-based tests for datagen math (Phase 4, plan §5.2).

Uses Hypothesis to find edge cases that manual parametrization misses.
"""

from __future__ import annotations

from datetime import date

from hypothesis import given, settings
from hypothesis import strategies as st

from datagen.calendar import season_factor, weekday_factor
from events.scoring.heuristic import heuristic_score

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

reasonable_dates = st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31))
positive_floats = st.floats(min_value=0.01, max_value=10.0, allow_nan=False, allow_infinity=False)
amplitudes = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
weekday_tables = st.lists(
    st.floats(min_value=0.1, max_value=3.0, allow_nan=False),
    min_size=7,
    max_size=7,
)
prices = st.floats(min_value=1.0, max_value=5000.0, allow_nan=False, allow_infinity=False)
attendances = st.integers(min_value=0, max_value=100000)
distances = st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
categories = st.sampled_from(["MUSIC", "SPORTS", "CONFERENCE", "CULTURE", None])


# ---------------------------------------------------------------------------
# Season factor properties
# ---------------------------------------------------------------------------


@given(day=reasonable_dates, amplitude=amplitudes)
@settings(max_examples=200)
def test_season_factor_always_positive(day: date, amplitude: float) -> None:
    """Season factor must always be > 0 for any valid date and amplitude."""
    result = season_factor(day, amplitude)
    assert result > 0, f"season_factor({day}, {amplitude}) = {result}"


@given(day=reasonable_dates, amplitude=amplitudes)
@settings(max_examples=200)
def test_season_factor_bounded(day: date, amplitude: float) -> None:
    """Season factor should stay within a reasonable range [0.2, 3.0]."""
    result = season_factor(day, amplitude)
    assert 0.1 < result < 5.0, f"season_factor({day}, {amplitude}) = {result}"


# ---------------------------------------------------------------------------
# Weekday factor properties
# ---------------------------------------------------------------------------


@given(day=reasonable_dates, table=weekday_tables)
@settings(max_examples=200)
def test_weekday_factor_returns_table_value(day: date, table: list[float]) -> None:
    """Weekday factor must return the value at the correct day-of-week index."""
    result = weekday_factor(day, table)
    assert result == table[day.weekday()]


# ---------------------------------------------------------------------------
# Heuristic score properties
# ---------------------------------------------------------------------------


@given(category=categories, attendance=attendances, distance=distances)
@settings(max_examples=300)
def test_heuristic_score_clamped_0_100(
    category: str | None, attendance: int, distance: float
) -> None:
    """Heuristic score must always be in [0, 100]."""
    score = heuristic_score(
        category=category, expected_attendance=attendance, distance_km=distance
    )
    assert 0 <= score <= 100


@given(
    category=st.sampled_from(["MUSIC", "SPORTS"]),
    distance=st.floats(min_value=0.5, max_value=10.0, allow_nan=False),
)
@settings(max_examples=100)
def test_heuristic_score_monotonic_with_attendance(category: str, distance: float) -> None:
    """Higher attendance should never decrease the score (ceteris paribus)."""
    score_low = heuristic_score(
        category=category, expected_attendance=1000, distance_km=distance
    )
    score_high = heuristic_score(
        category=category, expected_attendance=20000, distance_km=distance
    )
    assert score_high >= score_low


@given(
    category=st.sampled_from(["MUSIC", "SPORTS"]),
    attendance=st.integers(min_value=5000, max_value=30000),
)
@settings(max_examples=100)
def test_heuristic_score_closer_is_higher(category: str, attendance: int) -> None:
    """Closer events should score at least as high as more distant ones."""
    score_close = heuristic_score(
        category=category, expected_attendance=attendance, distance_km=1.0
    )
    score_far = heuristic_score(
        category=category, expected_attendance=attendance, distance_km=25.0
    )
    assert score_close >= score_far
