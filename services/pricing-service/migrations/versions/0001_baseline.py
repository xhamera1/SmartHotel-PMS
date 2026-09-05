"""pricing schema baseline

Revision ID: 0001
Revises:
Create Date: 2026-09-05

Five tables (see docs/diagrams/erd-pricing.md):
  events          — external events (Ticketmaster/static), deduplicated per provider
  event_scores    — LLM impact scores per event (history kept; latest wins)
  daily_demand    — aggregated DemandIndicator per HotelNight
  model_registry  — trained model artifacts; at most ONE active (partial unique index)
  prediction_log  — append-only log of every model prediction served

No foreign keys into the pms schema — cross-service integrity is by contract,
not by database coupling (ADR-0002).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "pricing"


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger, sa.Identity(always=True), primary_key=True),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("external_id", sa.String(100), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("category", sa.String(50)),
        sa.Column("venue_name", sa.String(200)),
        sa.Column("city", sa.String(100)),
        sa.Column("latitude", sa.Numeric(9, 6)),
        sa.Column("longitude", sa.Numeric(9, 6)),
        sa.Column("distance_km", sa.Numeric(6, 2)),
        sa.Column("starts_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("ends_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("expected_attendance", sa.Integer),
        sa.Column("url", sa.Text),
        sa.Column("raw_payload", postgresql.JSONB, nullable=False),
        sa.Column(
            "fetched_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("content_hash", sa.String(64), nullable=False),  # sha256 hex of raw_payload
        sa.Column("status", sa.String(10), nullable=False, server_default="NEW"),
        sa.CheckConstraint("status IN ('NEW','SCORED','STALE','IGNORED')", name="ck_events_status"),
        sa.UniqueConstraint("provider", "external_id", name="uq_events_provider_external_id"),
        schema=SCHEMA,
    )
    op.create_index("ix_events_status", "events", ["status"], schema=SCHEMA)
    op.create_index("ix_events_starts_at", "events", ["starts_at"], schema=SCHEMA)

    op.create_table(
        "event_scores",
        sa.Column("id", sa.BigInteger, sa.Identity(always=True), primary_key=True),
        sa.Column(
            "event_id",
            sa.BigInteger,
            sa.ForeignKey(f"{SCHEMA}.events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("impact_score", sa.SmallInteger, nullable=False),
        sa.Column("confidence", sa.Numeric(3, 2)),
        sa.Column("affected_nights", postgresql.ARRAY(sa.Date), nullable=False),
        sa.Column("rationale", sa.Text),
        sa.Column("llm_model", sa.Text),
        sa.Column("prompt_version", sa.Text),
        sa.Column("response_raw", postgresql.JSONB),
        sa.Column("is_fallback", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column(
            "scored_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("impact_score BETWEEN 0 AND 100", name="ck_event_scores_impact_range"),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_event_scores_confidence_range",
        ),
        schema=SCHEMA,
    )
    op.create_index("ix_event_scores_event_id", "event_scores", ["event_id"], schema=SCHEMA)

    op.create_table(
        "daily_demand",
        sa.Column("date", sa.Date, primary_key=True),
        sa.Column("indicator", sa.SmallInteger, nullable=False),
        sa.Column(
            "top_event_ids",
            postgresql.ARRAY(sa.BigInteger),
            nullable=False,
            server_default=sa.text("'{}'::bigint[]"),
        ),
        sa.Column(
            "computed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("indicator BETWEEN 0 AND 100", name="ck_daily_demand_indicator_range"),
        schema=SCHEMA,
    )

    op.create_table(
        "model_registry",
        sa.Column("id", sa.BigInteger, sa.Identity(always=True), primary_key=True),
        sa.Column("version", sa.Text, nullable=False, unique=True),
        sa.Column("algorithm", sa.Text, nullable=False),
        sa.Column("dataset_hash", sa.Text, nullable=False),
        sa.Column("params", postgresql.JSONB, nullable=False),
        sa.Column("metrics", postgresql.JSONB, nullable=False),
        sa.Column("feature_schema_hash", sa.Text, nullable=False),
        sa.Column("artifact_path", sa.Text, nullable=False),
        sa.Column("trained_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("false")),
        schema=SCHEMA,
    )
    # Invariant: at most one active model, enforced by the database.
    op.create_index(
        "uq_model_registry_single_active",
        "model_registry",
        ["is_active"],
        unique=True,
        schema=SCHEMA,
        postgresql_where=sa.text("is_active"),
    )

    op.create_table(
        "prediction_log",
        sa.Column("id", sa.BigInteger, sa.Identity(always=True), primary_key=True),
        sa.Column("request_id", sa.Text, nullable=False),
        sa.Column("room_type_code", sa.String(30), nullable=False),
        sa.Column("stay_date", sa.Date, nullable=False),
        sa.Column("features", postgresql.JSONB, nullable=False),
        sa.Column("multiplier", sa.Numeric(6, 4), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("model_version", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        schema=SCHEMA,
    )
    op.create_index("ix_prediction_log_created_at", "prediction_log", ["created_at"], schema=SCHEMA)
    op.create_index("ix_prediction_log_request_id", "prediction_log", ["request_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_table("prediction_log", schema=SCHEMA)
    op.drop_table("model_registry", schema=SCHEMA)
    op.drop_table("daily_demand", schema=SCHEMA)
    op.drop_table("event_scores", schema=SCHEMA)
    op.drop_table("events", schema=SCHEMA)
