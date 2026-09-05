# pms-core

PMS core backend — Java 21 · Spring Boot · Maven.

Owns reservations, rooms, room types, guests, staff authentication (JWT), and the
rate calendar (precomputed prices with manual-override precedence). Owns the `pms`
PostgreSQL schema via Flyway. Talks to `pricing-service` through a resilient internal
REST client (Resilience4j) — never on the guest booking path.

The Phase 1 Maven module runs database integration tests. The Spring Boot
application is not scaffolded yet; Phase 2 builds on this module and its migrations:

- `src/main/resources/db/migration/V1__baseline.sql` — `pms` schema (Flyway; next
  schema migration starts at **V3**).
- `src/main/resources/db/seed/V2__seed_reference_data.sql` — dev/test seeds
  (rate plans, room types, 35 rooms, staff users); the dev/test Spring profiles
  add `classpath:db/seed` to `spring.flyway.locations`, prod does not.

ERD: `docs/diagrams/erd-pms.md` · state machine: `docs/diagrams/reservation-state-machine.md`
· API contract: `docs/api/pms-api.md`.

## Database integration tests

Requirements: JDK 21 and a running Docker engine (Docker Desktop / Linux containers
on Windows). The committed Apache Maven Wrapper pins Maven 3.9.16; no global Maven
installation is needed. The first run downloads Maven, dependencies, and container
images.

From the repository root:

```text
task test:java
task test           # infrastructure smoke + Java integration tests
```

Or from this directory: `mvnw.cmd -B -ntp verify` on Windows,
`sh ./mvnw -B -ntp verify` on Linux/macOS. Use **verify**, not just `test`:
Failsafe runs `*IT` classes during `integration-test` and checks their results at
`verify`. Missing tests or an unavailable Docker engine fail the build.

- `PmsMigrationIT`: empty-database migration, schema/constraint/generated-column
  assertions, explicit dev/test seeds, idempotent re-runs, and pre-existing infra
  schemas with `btree_gist` already installed in `public`.
- `ReservationConstraintsIT`: overlapping active statuses and date ranges,
  same-day turnover on either boundary, different rooms, terminal statuses
  releasing inventory, and conflicting status updates. Rejections must identify
  SQLSTATE `23P01` and the `no_double_booking` constraint specifically.

Tests use only disposable PostgreSQL 17 Testcontainers; they do not connect to the
Compose database or use `.env` credentials. Each migration test gets a fresh
container; constraint tests share one container and roll back each test transaction.
They exercise the real migration files under `src/main/resources`, not copies of
the schema. Reports are written to `target/failsafe-reports` and uploaded by CI.

JUnit 5, Flyway and JDBC are used directly, before Spring/JPA exists. Checkstyle,
SpotBugs and application coverage gates arrive with the Phase 2 application code.
