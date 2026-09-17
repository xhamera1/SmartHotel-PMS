"""Latent nightly demand, bookings, and revenue-optimal prices (Phase 4 steps 4–5)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from datagen.config import DatagenConfig, RoomTypeConfig
from datagen.events import SyntheticEvent

# Expected booking *attempts* per sellable room before calendar/event/noise scaling.
# With ~50% conversion at BAR≈WTP this targets ~65–75% occupied room-nights.
BASE_ATTEMPTS_PER_ROOM = 1.35

# Stay-length distribution (nights): leisure city short stays.
STAY_LENGTH_DAYS = (1, 2, 3, 4)
STAY_LENGTH_PROBS = (0.45, 0.35, 0.15, 0.05)

# Grid step (PLN) for p* search within [min_price, max_price] (ADR-0009 grosz via round).
PRICE_GRID_STEP = 1.0


@dataclass(frozen=True)
class NightDemand:
    day: date
    room_type: str
    base_price: float
    rooms: int
    elasticity: float
    season_factor: float
    weekday_factor: float
    holiday_factor: float
    event_uplift: float
    """Sum of overlapping events' true_uplift (0 = none)."""
    demand_latent: float
    """Expected attempt intensity D = base × season × weekday × holiday × (1+event) × exp(ε)."""
    eps_total: float
    """ε = ε_obs + ε_latent (latent part is invisible to later ML features)."""

    @property
    def willingness_to_pay(self) -> float:
        """True WTP under the simulator world state (includes latent ε)."""
        event_mult = 1.0 + self.event_uplift
        return float(
            self.base_price
            * self.season_factor
            * self.weekday_factor
            * self.holiday_factor
            * event_mult
            * math.exp(self.eps_total)
        )


def event_uplift_by_date(events: list[SyntheticEvent], day: date) -> float:
    """Aggregate true uplifts of events covering ``day`` (additive)."""
    return float(sum(e.true_uplift for e in events if e.start_date <= day <= e.end_date))


def latent_demand(
    *,
    rooms: int,
    season: float,
    weekday: float,
    holiday: float,
    event_uplift: float,
    eps: float,
    base_attempts_per_room: float = BASE_ATTEMPTS_PER_ROOM,
) -> float:
    """
    D(date, roomType) = base × season × weekday × holiday × event_mult × exp(ε).

    ``event_mult = 1 + event_uplift`` so a night with no events keeps multiplier 1.
    """
    if rooms <= 0:
        raise ValueError("rooms must be positive")
    base = rooms * base_attempts_per_room
    event_mult = 1.0 + max(event_uplift, 0.0)
    return float(base * season * weekday * holiday * event_mult * math.exp(eps))


def conversion_probability(price: float, wtp: float, elasticity: float) -> float:
    """Logistic conversion vs willingness-to-pay (elasticity from room-type config)."""
    if price <= 0 or wtp <= 0:
        return 0.0
    if elasticity <= 0:
        raise ValueError("elasticity must be positive")
    # P=0.5 when price=wtp; higher elasticity → sharper drop when price > wtp.
    return float(1.0 / (1.0 + math.exp(elasticity * (price - wtp) / wtp)))


def expected_bookings_at_price(night: NightDemand, price: float) -> float:
    """
    Capacity-constrained expected sold rooms at ``price`` under the true demand.

    E[bookings] ≈ min(rooms, D · π(price, WTP, elasticity)).
    Cancellations are price-independent so they do not affect argmax_p.
    """
    pi = conversion_probability(price, night.willingness_to_pay, night.elasticity)
    return float(min(night.rooms, night.demand_latent * pi))


def expected_revenue_at_price(night: NightDemand, price: float) -> float:
    """p · E[bookings(p)] — the objective maximized for the ML target (D7)."""
    return float(price * expected_bookings_at_price(night, price))


def price_grid(min_price: float, max_price: float, step: float = PRICE_GRID_STEP) -> np.ndarray:
    """Inclusive PLN grid from min to max (last point always max_price)."""
    if step <= 0:
        raise ValueError("step must be positive")
    if min_price > max_price:
        raise ValueError("min_price must be ≤ max_price")
    prices = np.arange(min_price, max_price + step * 0.5, step, dtype=np.float64)
    if prices.size == 0 or prices[-1] < max_price - 1e-9:
        prices = np.append(prices, max_price)
    else:
        prices[-1] = max_price
    return np.round(prices, 2)


def optimal_price_for_night(
    night: NightDemand,
    *,
    min_price: float,
    max_price: float,
    step: float = PRICE_GRID_STEP,
) -> tuple[float, float]:
    """
    Grid-search ``p* = argmax_p p · E[bookings(p)]`` in ``[min_price, max_price]``.

    Returns ``(optimal_price, price_multiplier)`` with ``m* = p* / base_price``.
    On revenue ties, the lower price wins (iterate ascending, strict ``>``).
    """
    if night.base_price <= 0:
        raise ValueError("base_price must be positive")
    best_price = float(min_price)
    best_rev = expected_revenue_at_price(night, best_price)
    for price in price_grid(min_price, max_price, step):
        rev = expected_revenue_at_price(night, float(price))
        if rev > best_rev:
            best_rev = rev
            best_price = float(price)
    multiplier = best_price / night.base_price
    return best_price, float(multiplier)


def assign_optimal_prices(
    nights: list[NightDemand],
    room_types: list[RoomTypeConfig],
    *,
    step: float = PRICE_GRID_STEP,
) -> list[tuple[float, float]]:
    """Per-night ``(p*, m*)`` using each room type's min/max guardrails."""
    by_code = {rt.code: rt for rt in room_types}
    out: list[tuple[float, float]] = []
    for night in nights:
        rt = by_code[night.room_type]
        out.append(
            optimal_price_for_night(
                night,
                min_price=rt.min_price,
                max_price=rt.max_price,
                step=step,
            )
        )
    return out


def build_night_demands(
    config: DatagenConfig,
    calendar: pd.DataFrame,
    events: list[SyntheticEvent],
    rng: np.random.Generator,
) -> list[NightDemand]:
    """One latent-demand row per (date, room type) with split noise shocks."""
    cal = calendar.copy()
    cal["date_key"] = pd.to_datetime(cal["date"]).dt.date

    nights: list[NightDemand] = []
    for row in cal.itertuples(index=False):
        day: date = row.date_key  # type: ignore[assignment]
        event_up = event_uplift_by_date(events, day)
        for rt in config.hotel.room_types:
            eps_obs = float(rng.normal(0.0, config.demand.noise_sigma))
            eps_lat = float(rng.normal(0.0, config.demand.latent_shock_sigma))
            eps = eps_obs + eps_lat
            demand = latent_demand(
                rooms=rt.rooms,
                season=float(row.season_factor),
                weekday=float(row.weekday_factor),
                holiday=float(row.holiday_factor),
                event_uplift=event_up,
                eps=eps,
            )
            nights.append(
                NightDemand(
                    day=day,
                    room_type=rt.code,
                    base_price=rt.base_price,
                    rooms=rt.rooms,
                    elasticity=rt.elasticity,
                    season_factor=float(row.season_factor),
                    weekday_factor=float(row.weekday_factor),
                    holiday_factor=float(row.holiday_factor),
                    event_uplift=event_up,
                    demand_latent=demand,
                    eps_total=eps,
                )
            )
    return nights


def nights_to_frame(
    nights: list[NightDemand],
    *,
    room_types: list[RoomTypeConfig] | None = None,
    step: float = PRICE_GRID_STEP,
) -> pd.DataFrame:
    """
    Nightly demand table. When ``room_types`` is provided, fills ``optimal_price``
    and ``price_multiplier`` via revenue grid search (step 5 / D7).
    """
    if not nights:
        return pd.DataFrame(
            {
                "date": pd.Series(dtype="datetime64[ns]"),
                "room_type": pd.Series(dtype="string"),
                "base_price": pd.Series(dtype="float64"),
                "demand_latent": pd.Series(dtype="float64"),
                "event_uplift": pd.Series(dtype="float64"),
                "optimal_price": pd.Series(dtype="float64"),
                "price_multiplier": pd.Series(dtype="float64"),
            }
        )

    if room_types is None:
        optimal_prices = [float("nan")] * len(nights)
        multipliers = [float("nan")] * len(nights)
    else:
        optima = assign_optimal_prices(nights, room_types, step=step)
        optimal_prices = [p for p, _ in optima]
        multipliers = [m for _, m in optima]

    return pd.DataFrame(
        {
            "date": pd.to_datetime([n.day for n in nights]),
            "room_type": [n.room_type for n in nights],
            "base_price": [n.base_price for n in nights],
            "demand_latent": [n.demand_latent for n in nights],
            "event_uplift": [n.event_uplift for n in nights],
            "optimal_price": optimal_prices,
            "price_multiplier": multipliers,
        }
    )


def simulate_bookings(
    config: DatagenConfig,
    nights: list[NightDemand],
    rng: np.random.Generator,
) -> pd.DataFrame:
    """
    Poisson attempts per (stay-start night, room type), gamma lead times, logistic
    conversion, capacity constraints, Bernoulli cancellations.
    """
    inventory: dict[tuple[date, str], int] = {(n.day, n.room_type): n.rooms for n in nights}
    horizon_end = config.horizon.end
    shape = config.booking.lead_time_gamma.shape
    scale = config.booking.lead_time_gamma.scale
    cancel_p = config.booking.cancellation_rate

    candidates: list[dict[str, object]] = []

    for night in nights:
        n_attempts = int(rng.poisson(max(night.demand_latent, 0.0)))
        for _ in range(n_attempts):
            stay_len = int(rng.choice(STAY_LENGTH_DAYS, p=STAY_LENGTH_PROBS))
            check_in = night.day
            check_out = check_in + timedelta(days=stay_len)
            if check_out - timedelta(days=1) > horizon_end:
                # Truncate stay to remain inside the simulated horizon.
                stay_len = (horizon_end - check_in).days + 1
                if stay_len < 1:
                    continue
                check_out = check_in + timedelta(days=stay_len)

            lead = max(0, int(round(float(rng.gamma(shape, scale)))))
            booked_at = check_in - timedelta(days=lead)

            # WTP shares multiplicative world state (incl. ε) so high-demand nights
            # also tolerate higher prices; quoted price is BAR = base_price.
            price = night.base_price
            p_book = conversion_probability(price, night.willingness_to_pay, night.elasticity)
            if rng.random() > p_book:
                continue

            candidates.append(
                {
                    "room_type": night.room_type,
                    "check_in": check_in,
                    "check_out": check_out,
                    "booked_at": booked_at,
                    "nights": stay_len,
                    "price_night": price,
                    "capacity_keys": [
                        (check_in + timedelta(days=i), night.room_type) for i in range(stay_len)
                    ],
                }
            )

    # Chronological acceptance ≈ realistic inventory.
    candidates.sort(key=lambda c: (c["booked_at"], c["check_in"], c["room_type"]))  # type: ignore[arg-type, index]

    rows: list[dict[str, object]] = []
    booking_seq = 0
    for cand in candidates:
        keys: list[tuple[date, str]] = cand["capacity_keys"]  # type: ignore[assignment]
        if any(inventory.get(k, 0) <= 0 for k in keys):
            continue
        # All nights must exist in the simulated inventory map.
        if any(k not in inventory for k in keys):
            continue

        for k in keys:
            inventory[k] -= 1

        cancelled = bool(rng.random() < cancel_p)
        if cancelled:
            for k in keys:
                inventory[k] += 1

        booking_seq += 1
        stay_nights = int(cand["nights"])  # type: ignore[arg-type]
        price_night = float(cand["price_night"])  # type: ignore[arg-type]
        rows.append(
            {
                "booking_id": f"BKG-{booking_seq:06d}",
                "room_type": cand["room_type"],
                "check_in": cand["check_in"],
                "check_out": cand["check_out"],
                "booked_at": cand["booked_at"],
                "nights": stay_nights,
                "price_total": round(price_night * stay_nights, 2),
                "cancelled": cancelled,
            }
        )

    if not rows:
        return pd.DataFrame(
            {
                "booking_id": pd.Series(dtype="string"),
                "room_type": pd.Series(dtype="string"),
                "check_in": pd.Series(dtype="datetime64[ns]"),
                "check_out": pd.Series(dtype="datetime64[ns]"),
                "booked_at": pd.Series(dtype="datetime64[ns]"),
                "nights": pd.Series(dtype="int64"),
                "price_total": pd.Series(dtype="float64"),
                "cancelled": pd.Series(dtype="bool"),
            }
        )

    frame = pd.DataFrame(rows)
    frame["check_in"] = pd.to_datetime(frame["check_in"])
    frame["check_out"] = pd.to_datetime(frame["check_out"])
    frame["booked_at"] = pd.to_datetime(frame["booked_at"])
    return frame
