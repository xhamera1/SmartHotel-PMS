"""Alembic environment for the `pricing` schema.

The pricing service owns ONLY the `pricing` schema (ADR-0002) — the Alembic
version table lives there too, keeping the `pms` schema (Flyway-owned)
completely untouched. The database URL is read from PRICING_DATABASE_URL and
is never hardcoded.
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool, text

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

VERSION_TABLE_SCHEMA = "pricing"

# Autogenerate support arrives with the SQLAlchemy models (service scaffold).
target_metadata = None


def _database_url() -> str:
    url = os.environ.get("PRICING_DATABASE_URL")
    if not url:
        raise RuntimeError(
            "PRICING_DATABASE_URL is not set — see .env.example "
            "(e.g. postgresql+psycopg://pricing_user:...@localhost:5432/smarthotel)"
        )
    return url


def _ensure_schema(connection) -> None:
    """Create the pricing schema on pristine databases (CI, Testcontainers).

    In dev the schema already exists, owned by pricing_user (infra/postgres/init),
    so this is skipped — important because pricing_user has no CREATE privilege
    on the database itself (least privilege).
    """
    exists = connection.execute(
        text("SELECT 1 FROM information_schema.schemata WHERE schema_name = :s"),
        {"s": VERSION_TABLE_SCHEMA},
    ).scalar()
    if not exists:
        connection.execute(text(f"CREATE SCHEMA {VERSION_TABLE_SCHEMA}"))
    # ALWAYS commit — even when nothing was created. The SELECT above opens
    # SQLAlchemy's implicit (autobegin) transaction; if it is left open, Alembic
    # assumes the caller manages the transaction and skips its own COMMIT, so the
    # whole migration silently rolls back on connection close (DEF-0003).
    connection.commit()


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=VERSION_TABLE_SCHEMA,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        _ensure_schema(connection)
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=VERSION_TABLE_SCHEMA,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
