# ADR-0002: One PostgreSQL instance, two isolated schemas

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Patryk Chamera
- **Plan reference:** D2

## Context and Problem Statement

Microservices best practice is database-per-service: `pms-core` and
`pricing-service` must not share tables or couple through the database. Operating
two database clusters, however, doubles the infrastructure burden for a solo
developer on a laptop and in CI.

## Considered Options

1. Two separate PostgreSQL instances (strict database-per-service)
2. One instance, one database, two schemas with least-privilege users
3. One shared schema for both services

## Decision Outcome

**Chosen option:** one instance with schemas `pms` and `pricing`, each owned by a
dedicated login role (`pms_user`, `pricing_user`) that has no privileges on the
other schema. This demonstrates the database-per-service *pattern* (no cross-service
data coupling is possible — verified: cross-schema access fails with
`permission denied`) at a fraction of the operational cost. Option 3 rejected as an
antipattern; option 1 rejected as cost without benefit at this scale.

### Consequences

- Good: single container/backup/port locally and in CI; pattern intact.
- Good: migrations are independent (Flyway owns `pms`, Alembic owns `pricing`).
- Bad / risk: temptation to "just join across schemas" — technically blocked by
  grants; also forbidden by convention (services talk only via APIs, ADR-0005).
- Note: shared extensions (`btree_gist`) live in `public`, which stays on both
  roles' `search_path`.

## More Information

Init script: `infra/postgres/init/01-init.sh`. Smoke checks: `task smoke`.
