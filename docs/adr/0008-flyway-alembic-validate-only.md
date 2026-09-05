# ADR-0008: Flyway for pms, Alembic for pricing, ORM validate-only

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Patryk Chamera
- **Plan reference:** D15

## Context and Problem Statement

Two services own two schemas in one PostgreSQL instance. Schema changes must be
reviewable, testable in CI, and independent per service. Letting an ORM invent
or mutate tables at runtime would undermine the QA focus of the thesis.

## Considered Options

1. Hibernate / SQLAlchemy auto-create (`ddl-auto=update` / `create_all`)
2. Flyway for `pms`, Alembic for `pricing`; ORM set to validate only
3. A single shared migration tool across both languages

## Decision Outcome

**Chosen option:** Flyway owns `pms` (Java); Alembic owns `pricing` (Python).
Hibernate (and any SQLAlchemy metadata) runs in **validate** mode only — never
create/update. Dev/test may additionally load Flyway seed scripts; production
loads schema migrations only.

### Consequences

- Good: migrations are code-reviewed, idempotent, and exercised by CI
  (Testcontainers / Alembic cycle).
- Good: service ownership of schemas stays clear (ADR-0002).
- Bad / risk: two tools to learn — acceptable; each stays in its language ecosystem.

## More Information

Baselines: `services/pms-core/.../V1__baseline.sql`,
`services/pricing-service/migrations/versions/0001_baseline.py`.
