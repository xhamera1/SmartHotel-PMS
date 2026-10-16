"""Alembic migration cycle test (Phase 1 — local pytest coverage).

Runs upgrade → re-upgrade (idempotent) → downgrade → upgrade against a
real PostgreSQL container, then asserts the pricing schema is correct.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
import sqlalchemy as sa

ALEMBIC_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_TABLES = {
    "alembic_version",
    "events",
    "event_scores",
    "daily_demand",
    "model_registry",
    "prediction_log",
}


@pytest.fixture(scope="module")
def pg_url() -> Iterator[str]:
    pytest.importorskip("testcontainers")
    try:
        from testcontainers.community.postgres import PostgresContainer
    except ImportError:
        from testcontainers.postgres import PostgresContainer

    try:
        postgres = PostgresContainer("postgres:17")
        postgres.start()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Docker/testcontainers unavailable: {exc}")

    try:
        url = postgres.get_connection_url()
        yield url.replace("psycopg2", "psycopg")
    finally:
        postgres.stop()


def _alembic(pg_url: str, *args: str) -> subprocess.CompletedProcess[str]:
    """Run alembic CLI in a subprocess with the correct env."""
    env = {**os.environ, "PRICING_DATABASE_URL": pg_url}
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=str(ALEMBIC_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _get_tables(pg_url: str) -> set[str]:
    engine = sa.create_engine(pg_url)
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                sa.text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'pricing'"
                )
            )
            return {r[0] for r in rows}
    finally:
        engine.dispose()


@pytest.mark.integration
def test_alembic_upgrade_downgrade_cycle(pg_url: str) -> None:
    """Full migration cycle: up → re-up → down → up."""
    # 1. upgrade head
    result = _alembic(pg_url, "upgrade", "head")
    assert result.returncode == 0, f"upgrade head failed: {result.stderr}"

    tables = _get_tables(pg_url)
    missing = EXPECTED_TABLES - tables
    assert not missing, f"Missing tables after upgrade: {missing}"

    # 2. idempotent re-upgrade
    result = _alembic(pg_url, "upgrade", "head")
    assert result.returncode == 0, f"re-upgrade failed: {result.stderr}"

    # 3. downgrade to base
    result = _alembic(pg_url, "downgrade", "base")
    assert result.returncode == 0, f"downgrade failed: {result.stderr}"

    tables_after_down = _get_tables(pg_url)
    remaining_data = EXPECTED_TABLES & tables_after_down - {"alembic_version"}
    assert not remaining_data, f"Tables still present after downgrade: {remaining_data}"

    # 4. re-upgrade from base
    result = _alembic(pg_url, "upgrade", "head")
    assert result.returncode == 0, f"re-upgrade from base failed: {result.stderr}"

    tables_final = _get_tables(pg_url)
    missing_final = EXPECTED_TABLES - tables_final
    assert not missing_final, f"Missing tables after re-upgrade: {missing_final}"
