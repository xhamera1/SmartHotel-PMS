"""Calendar demand factors: seasonality, weekdays, Polish holidays, bridge days."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache

import holidays
import pandas as pd

from datagen.config import DemandConfig, HorizonConfig

# Friday/Saturday-high leisure city profile is supplied via config weekday_multipliers.
# Bridge days get a fraction of holiday_boost (Appendix C only names holiday_boost).
DEFAULT_BRIDGE_RATIO = 0.5


@dataclass(frozen=True)
class DayFactors:
    day: date
    season_factor: float
    weekday_factor: float
    is_holiday: bool
    is_bridge: bool
    holiday_factor: float
    """Multiplier from holiday / bridge (1.0 on ordinary days)."""

    @property
    def calendar_factor(self) -> float:
        """Combined calendar multiplier before event uplift / noise."""
        return self.season_factor * self.weekday_factor * self.holiday_factor


def _day_of_year(day: date) -> int:
    return day.timetuple().tm_yday


def season_factor(day: date, amplitude: float, *, december_peak: float | None = None) -> float:
    """
    Annual seasonality: smooth sinusoid peaking mid-July, plus a December/New-Year bump.

    The sinusoid is ``1 + amplitude * sin(2π (doy - 105) / 365.25)`` so the peak falls
    near day-of-year 196 (~15 July). The December component is a Gaussian around 27 Dec
    that also covers early January.
    """
    if amplitude < 0:
        raise ValueError("season_amplitude must be >= 0")

    doy = _day_of_year(day)
    summer = 1.0 + amplitude * math.sin(2.0 * math.pi * (doy - 105.0) / 365.25)

    peak = amplitude * 0.6 if december_peak is None else december_peak
    if day.month == 12 and day.day >= 15:
        dist = abs(day.day - 27)
        december = peak * math.exp(-0.5 * (dist / 6.0) ** 2)
    elif day.month == 1 and day.day <= 6:
        # Continuity past New Year (27 Dec → day 0 of the bump axis).
        dist = day.day + (31 - 27)
        december = peak * math.exp(-0.5 * (dist / 6.0) ** 2)
    else:
        december = 0.0

    # Keep strictly positive for multiplicative demand models.
    return max(summer + december, 1e-3)


def weekday_factor(day: date, multipliers: list[float]) -> float:
    """Map date → Mon..Sun multiplier (index 0 = Monday)."""
    if len(multipliers) != 7:
        raise ValueError("weekday_multipliers must have length 7 (Mon..Sun)")
    return float(multipliers[day.weekday()])


@lru_cache(maxsize=32)
def polish_holidays_for_years(years: tuple[int, ...]) -> frozenset[date]:
    """Cached Polish public-holiday set for the given calendar years."""
    pl = holidays.country_holidays("PL", years=years)
    return frozenset(pl.keys())


def holiday_set_for_horizon(start: date, end: date) -> frozenset[date]:
    years = tuple(range(start.year, end.year + 1))
    return polish_holidays_for_years(years)


def is_polish_holiday(day: date, holiday_dates: frozenset[date] | None = None) -> bool:
    if holiday_dates is None:
        holiday_dates = polish_holidays_for_years((day.year,))
    return day in holiday_dates


def is_bridge_day(day: date, holiday_dates: frozenset[date]) -> bool:
    """
    Long-weekend "bridge" (most) day: a weekday that connects a public holiday to a weekend.

    Detects the common Polish patterns:
    - Thursday holiday → Friday bridge
    - Tuesday holiday → Monday bridge
    - Friday holiday → Thursday bridge
    - Monday holiday → Tuesday bridge
    """
    if day in holiday_dates or day.weekday() >= 5:
        return False

    yesterday = day - timedelta(days=1)
    tomorrow = day + timedelta(days=1)
    wd = day.weekday()

    if wd == 4 and yesterday in holiday_dates:  # Friday after Thursday holiday
        return True
    if wd == 0 and tomorrow in holiday_dates:  # Monday before Tuesday holiday
        return True
    if wd == 3 and tomorrow in holiday_dates:  # Thursday before Friday holiday
        return True
    # Tuesday after Monday holiday
    return wd == 1 and yesterday in holiday_dates


def holiday_factor(
    day: date,
    holiday_boost: float,
    holiday_dates: frozenset[date],
    *,
    bridge_ratio: float = DEFAULT_BRIDGE_RATIO,
) -> tuple[float, bool, bool]:
    """
    Return ``(multiplier, is_holiday, is_bridge)``.

    Holidays take precedence over bridge classification.
    """
    if holiday_boost < 0:
        raise ValueError("holiday_boost must be >= 0")
    if not 0.0 <= bridge_ratio <= 1.0:
        raise ValueError("bridge_ratio must be in [0, 1]")

    holiday = is_polish_holiday(day, holiday_dates)
    if holiday:
        return 1.0 + holiday_boost, True, False

    bridge = is_bridge_day(day, holiday_dates)
    if bridge:
        return 1.0 + holiday_boost * bridge_ratio, False, True

    return 1.0, False, False


def day_factors(
    day: date,
    demand: DemandConfig,
    holiday_dates: frozenset[date],
    *,
    bridge_ratio: float = DEFAULT_BRIDGE_RATIO,
) -> DayFactors:
    season = season_factor(day, demand.season_amplitude)
    weekday = weekday_factor(day, demand.weekday_multipliers)
    h_mult, is_hol, is_br = holiday_factor(
        day,
        demand.holiday_boost,
        holiday_dates,
        bridge_ratio=bridge_ratio,
    )
    return DayFactors(
        day=day,
        season_factor=season,
        weekday_factor=weekday,
        is_holiday=is_hol,
        is_bridge=is_br,
        holiday_factor=h_mult,
    )


def iter_dates(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def build_calendar_frame(
    horizon: HorizonConfig,
    demand: DemandConfig,
    *,
    bridge_ratio: float = DEFAULT_BRIDGE_RATIO,
) -> pd.DataFrame:
    """One row per night in the horizon with all calendar factor columns."""
    holiday_dates = holiday_set_for_horizon(horizon.start, horizon.end)
    rows: list[dict[str, object]] = []
    for day in iter_dates(horizon.start, horizon.end):
        factors = day_factors(day, demand, holiday_dates, bridge_ratio=bridge_ratio)
        rows.append(
            {
                "date": pd.Timestamp(factors.day),
                "season_factor": factors.season_factor,
                "weekday_factor": factors.weekday_factor,
                "holiday_flag": int(factors.is_holiday),
                "bridge_flag": int(factors.is_bridge),
                "holiday_factor": factors.holiday_factor,
                "calendar_factor": factors.calendar_factor,
            }
        )
    return pd.DataFrame(rows)
