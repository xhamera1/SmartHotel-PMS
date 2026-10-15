"""Price clamping and half-up rounding to whole PLN."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def clamp_and_round(
    *,
    base_price: float,
    multiplier: float,
    min_price: float,
    max_price: float,
) -> tuple[Decimal, float]:
    """
    Apply model multiplier, clamp to ``[min_price, max_price]``, round once.

    Model math stays in float; the returned price is a ``Decimal`` with scale 0
    (whole PLN, half-up). Served multiplier is ``price / base_price``.
    """
    if base_price <= 0:
        raise ValueError("base_price must be positive")
    if min_price <= 0 or max_price <= 0:
        raise ValueError("min_price and max_price must be positive")
    if min_price > max_price:
        raise ValueError("min_price must be <= max_price")
    if not (min_price <= base_price <= max_price):
        raise ValueError("base_price must lie within [min_price, max_price]")

    raw = float(base_price) * float(multiplier)
    clamped = min(max(raw, float(min_price)), float(max_price))
    price = Decimal(str(clamped)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    served_multiplier = float(price) / float(base_price)
    return price, served_multiplier
