#!/bin/sh
# =============================================================================
# SmartHotel-PMS — PostgreSQL first-run initialization (Phase 0.4, decision D2)
#
# Creates the two service schemas and their least-privilege login users:
#   pms_user     → owns schema pms      (used by pms-core / Flyway)
#   pricing_user → owns schema pricing  (used by pricing-service / Alembic)
# Neither user can access the other's schema — the database-per-service
# pattern on a single instance.
#
# Executed by the official postgres image's docker-entrypoint-initdb.d
# contract, only when the data volume is initialized for the first time.
# (This script runs inside the Linux container — the "no bash-only scripts"
# rule applies to host-side developer tooling, not container internals.)
# =============================================================================
set -e

# Escape single quotes so passwords embed safely into SQL string literals.
sql_escape() { printf %s "$1" | sed "s/'/''/g"; }

PMS_PW="$(sql_escape "${PMS_DB_PASSWORD:?PMS_DB_PASSWORD is required}")"
PRICING_PW="$(sql_escape "${PRICING_DB_PASSWORD:?PRICING_DB_PASSWORD is required}")"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
-- Service login roles ---------------------------------------------------------
CREATE ROLE pms_user     LOGIN PASSWORD '${PMS_PW}';
CREATE ROLE pricing_user LOGIN PASSWORD '${PRICING_PW}';

-- Tighten database-level access (no implicit PUBLIC connect) ------------------
REVOKE ALL ON DATABASE ${POSTGRES_DB} FROM PUBLIC;
GRANT  CONNECT ON DATABASE ${POSTGRES_DB} TO pms_user, pricing_user;

-- One schema per service, owned by its user (full rights inside, none outside)
CREATE SCHEMA pms     AUTHORIZATION pms_user;
CREATE SCHEMA pricing AUTHORIZATION pricing_user;

-- Resolve objects in the own schema first; keep public reachable because the
-- btree_gist operator classes are installed there.
ALTER ROLE pms_user     SET search_path = pms, public;
ALTER ROLE pricing_user SET search_path = pricing, public;

-- Required by the no-double-booking exclusion constraint (plan §3.1).
-- Pre-created here by the superuser; the Flyway migration keeps
-- CREATE EXTENSION IF NOT EXISTS btree_gist; which then no-ops. Testcontainers
-- runs migrations as a superuser, so both environments behave identically.
CREATE EXTENSION IF NOT EXISTS btree_gist;
SQL

echo "SmartHotel init: schemas 'pms'/'pricing' and least-privilege users created."
