"""Synthetic event catalog with template text and true demand uplift (ground truth)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from datagen.config import DatagenConfig, EventCategory, EventsConfig, HorizonConfig

# Distance decay length-scale (km): venues beyond ~2–3× this contribute little.
DISTANCE_SCALE_KM = 6.0

# Typical Kraków venue distances from the hotel (km) — used as sampling anchors.
VENUE_DISTANCE_KM: dict[str, float] = {
    "Tauron Arena": 3.2,
    "ICE Kraków Congress Centre": 2.1,
    "Stadion Cracovia": 1.8,
    "Stadion Wisły": 2.4,
    "Teatr Słowackiego": 1.2,
    "Filharmonia Krakowska": 1.5,
    "Muzeum Narodowe": 1.0,
    "EXPO Kraków": 4.5,
    "Klub Studio": 2.8,
    "Centrum Kongresowe UP": 3.5,
}

CATEGORY_VENUES: dict[EventCategory, tuple[str, ...]] = {
    "MUSIC": ("Tauron Arena", "Klub Studio", "Filharmonia Krakowska", "ICE Kraków Congress Centre"),
    "SPORTS": ("Tauron Arena", "Stadion Cracovia", "Stadion Wisły"),
    "CONFERENCE": ("ICE Kraków Congress Centre", "EXPO Kraków", "Centrum Kongresowe UP"),
    "CULTURE": (
        "Teatr Słowackiego",
        "Muzeum Narodowe",
        "Filharmonia Krakowska",
        "ICE Kraków Congress Centre",
    ),
}

MUSIC_ARTISTS = (
    "Dawid Podsiadło",
    "Sanah",
    "Kwiat Jabłoni",
    "Daria Zawiałow",
    "Metallica",
    "Coldplay",
    "Imagine Dragons",
    "Krzysztof Penderecki Ensemble",
)

SPORTS_HOME = ("Cracovia", "Wisła Kraków", "Poland U21")
SPORTS_AWAY = (
    "Legia Warszawa",
    "Lech Poznań",
    "Śląsk Wrocław",
    "Raków Częstochowa",
    "Pogoń Szczecin",
)

CONFERENCE_TITLES = (
    "European Hospitality Tech Summit",
    "Central Europe AI Forum",
    "Kraków Tourism Leaders Meetup",
    "FinTech East Conference",
    "Sustainable Cities Symposium",
    "Medical Innovation Days",
)

CULTURE_SHOWS = (
    "Impressionists in Kraków",
    "Night of Museums Special Exhibition",
    "Ballet: Swan Lake",
    "Opera: Carmen",
    "Folk Traditions of Małopolska",
    "Contemporary Polish Photography",
)


@dataclass(frozen=True)
class SyntheticEvent:
    event_id: str
    category: EventCategory
    name: str
    description: str
    start_date: date
    end_date: date
    attendance: int
    distance_km: float
    true_uplift: float
    venue: str


def expected_event_count(horizon: HorizonConfig, per_year: int) -> int:
    """Scale Appendix C ``per_year`` by horizon length (~60/year → ~180 over 3 years)."""
    span_days = (horizon.end - horizon.start).days + 1
    return max(1, int(round(per_year * span_days / 365.25)))


def true_demand_uplift(
    *,
    attendance: int,
    distance_km: float,
    uplift_per_10k: float,
    distance_scale_km: float = DISTANCE_SCALE_KM,
) -> float:
    """
    Hidden ground-truth uplift used later as Gemini evaluation target (RQ3 / E3).

    ``uplift ≈ uplift_per_10k · (attendance / 10_000) · exp(-distance / scale)``
    """
    if attendance <= 0:
        raise ValueError("attendance must be positive")
    if distance_km < 0:
        raise ValueError("distance_km must be >= 0")
    if uplift_per_10k < 0:
        raise ValueError("uplift_per_10k must be >= 0")
    if distance_scale_km <= 0:
        raise ValueError("distance_scale_km must be > 0")

    size_term = uplift_per_10k * (attendance / 10_000.0)
    decay = float(np.exp(-distance_km / distance_scale_km))
    return float(size_term * decay)


def _sample_category(rng: np.random.Generator, events: EventsConfig) -> EventCategory:
    labels = list(events.categories.keys())
    probs = np.array([events.categories[c].share for c in labels], dtype=float)
    probs = probs / probs.sum()
    idx = int(rng.choice(len(labels), p=probs))
    return labels[idx]  # type: ignore[return-value]


def _sample_attendance(rng: np.random.Generator, low: int, high: int) -> int:
    return int(rng.integers(low, high + 1))


def _sample_distance_km(rng: np.random.Generator, venue: str) -> float:
    """Jitter around the venue's nominal distance (log-normal noise, clipped)."""
    base = VENUE_DISTANCE_KM[venue]
    jitter = float(rng.lognormal(mean=0.0, sigma=0.15))
    return float(np.clip(base * jitter, 0.3, 25.0))


def _sample_duration_days(rng: np.random.Generator) -> int:
    # Prefer 1-day events; allow 2–3 day festivals/conferences.
    return int(rng.choice([1, 2, 3], p=[0.70, 0.22, 0.08]))


def _render_text(
    rng: np.random.Generator,
    category: EventCategory,
    venue: str,
    attendance: int,
) -> tuple[str, str]:
    if category == "MUSIC":
        artist = str(rng.choice(MUSIC_ARTISTS))
        name = f"Concert of {artist} at {venue}"
        description = (
            f"{artist} performs live at {venue} in Kraków. "
            f"Expected attendance around {attendance:,} guests."
        )
        return name, description

    if category == "SPORTS":
        home = str(rng.choice(SPORTS_HOME))
        away = str(rng.choice(SPORTS_AWAY))
        name = f"{home} vs {away} at {venue}"
        description = (
            f"Football match: {home} hosts {away} at {venue}. "
            f"Stadium crowd estimated at {attendance:,}."
        )
        return name, description

    if category == "CONFERENCE":
        title = str(rng.choice(CONFERENCE_TITLES))
        name = f"{title} at {venue}"
        description = (
            f"Multi-session industry conference '{title}' held at {venue}. "
            f"About {attendance:,} delegates expected."
        )
        return name, description

    show = str(rng.choice(CULTURE_SHOWS))
    name = f"{show} at {venue}"
    description = (
        f"Cultural programme '{show}' at {venue} in Kraków. Projected attendance {attendance:,}."
    )
    return name, description


def generate_events(
    config: DatagenConfig,
    rng: np.random.Generator,
) -> list[SyntheticEvent]:
    """Sample the synthetic event catalog for the configured horizon."""
    n_events = expected_event_count(config.horizon, config.events.per_year)
    span_days = (config.horizon.end - config.horizon.start).days + 1
    events: list[SyntheticEvent] = []

    for i in range(n_events):
        category = _sample_category(rng, config.events)
        profile = config.events.categories[category]
        attendance = _sample_attendance(rng, profile.attendance[0], profile.attendance[1])
        venue = str(rng.choice(CATEGORY_VENUES[category]))
        distance_km = _sample_distance_km(rng, venue)
        duration = _sample_duration_days(rng)
        # Keep the whole multi-day event inside the horizon.
        max_start_offset = max(0, span_days - duration)
        start_offset = int(rng.integers(0, max_start_offset + 1))
        start = config.horizon.start + timedelta(days=start_offset)
        end = start + timedelta(days=duration - 1)
        name, description = _render_text(rng, category, venue, attendance)
        uplift = true_demand_uplift(
            attendance=attendance,
            distance_km=distance_km,
            uplift_per_10k=profile.uplift_per_10k,
        )
        events.append(
            SyntheticEvent(
                event_id=f"EVT-{i + 1:04d}",
                category=category,
                name=name,
                description=description,
                start_date=start,
                end_date=end,
                attendance=attendance,
                distance_km=round(distance_km, 3),
                true_uplift=uplift,
                venue=venue,
            )
        )

    events.sort(key=lambda e: (e.start_date, e.event_id))
    return events


def events_to_frame(events: list[SyntheticEvent]) -> pd.DataFrame:
    if not events:
        return pd.DataFrame(
            {
                "event_id": pd.Series(dtype="string"),
                "category": pd.Series(dtype="string"),
                "name": pd.Series(dtype="string"),
                "description": pd.Series(dtype="string"),
                "start_date": pd.Series(dtype="datetime64[ns]"),
                "end_date": pd.Series(dtype="datetime64[ns]"),
                "attendance": pd.Series(dtype="int64"),
                "distance_km": pd.Series(dtype="float64"),
                "true_uplift": pd.Series(dtype="float64"),
            }
        )

    return pd.DataFrame(
        {
            "event_id": [e.event_id for e in events],
            "category": [e.category for e in events],
            "name": [e.name for e in events],
            "description": [e.description for e in events],
            "start_date": pd.to_datetime([e.start_date for e in events]),
            "end_date": pd.to_datetime([e.end_date for e in events]),
            "attendance": [e.attendance for e in events],
            "distance_km": [e.distance_km for e in events],
            "true_uplift": [e.true_uplift for e in events],
        }
    )
