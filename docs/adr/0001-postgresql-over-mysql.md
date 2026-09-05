# ADR-0001: PostgreSQL 17 over MySQL

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Patryk Chamera
- **Plan reference:** D1, §3.1

## Context and Problem Statement

The thesis description leaves the database open ("MySQL or PostgreSQL"). The system
needs a relational store for two services, strong integrity guarantees for
reservations (no double bookings under concurrency), semi-structured storage for
event payloads / LLM responses / price breakdowns, and first-class support in the
test stack (Testcontainers, Flyway, Alembic).

## Considered Options

1. MySQL 8
2. PostgreSQL 17

## Decision Outcome

**Chosen option:** PostgreSQL 17, because it can enforce the core business
invariant at the database level: a GiST **exclusion constraint** on
`(room_id, daterange(check_in, check_out))` makes overlapping active reservations
impossible even under concurrent transactions — MySQL has no equivalent.

Supporting drivers: `JSONB` (event payloads, Gemini responses, price snapshots),
range types and window functions (occupancy analytics), a single engine serving
both services' schemas, and mature Testcontainers/Flyway/Alembic support.

### Consequences

- Good: double-booking prevention is a DB guarantee, not just application logic;
  a dedicated concurrency test will prove it (plan Phase 2).
- Good: JSONB keeps audit/raw-payload storage schema-light where appropriate.
- Bad / risk: exclusion constraints are less commonly known — mitigated by
  documentation (plan §3.1) and integration tests pinning the behavior.
- Note: `btree_gist` extension is required; it is pre-created by the compose init
  script and `CREATE EXTENSION IF NOT EXISTS` in migrations no-ops.

## More Information

Plan §3.1 contains the constraint DDL. Related: ADR-0002 (schema layout).
