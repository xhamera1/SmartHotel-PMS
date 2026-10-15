"""pytest-benchmark: 366-item quote batch (informational)."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.schemas import QuoteItemRequest
from app.services.model_loader import load_fixture_model
from app.services.quoting import quote_batch
from tests.api.conftest import FIXTURE_DIR


@pytest.fixture(scope="module")
def model():
    state = load_fixture_model(FIXTURE_DIR)
    assert state is not None
    return state


def _items(n: int = 366) -> list[QuoteItemRequest]:
    start = date(2024, 6, 1)
    out: list[QuoteItemRequest] = []
    for i in range(n):
        out.append(
            QuoteItemRequest(
                room_type_code="STD" if i % 2 == 0 else "DLX",
                date=start + timedelta(days=i % 60),
                base_price=250 if i % 2 == 0 else 420,
                min_price=180 if i % 2 == 0 else 300,
                max_price=450 if i % 2 == 0 else 800,
                occupancy_rate=(i % 10) / 10,
                rooms_remaining=max(0, 10 - (i % 10)),
                lead_time_days=[60, 30, 14, 7, 1][i % 5],
            )
        )
    return out


@pytest.mark.benchmark
def test_quote_batch_366_under_150ms(benchmark, model) -> None:
    engine = MagicMock()
    items = _items(366)
    request_id = uuid4()

    def run() -> None:
        with patch("app.services.quoting.fetch_demand_by_dates", return_value={}):
            quote_batch(engine=engine, model=model, request_id=request_id, items=items)

    benchmark(run)
    # Informational gate: p95-ish via benchmark stats when available.
    stats = getattr(benchmark, "stats", None)
    if stats is not None and hasattr(stats, "stats"):
        # pytest-benchmark stores seconds
        mean_ms = float(stats.stats.mean) * 1000.0
        assert mean_ms < 150.0
