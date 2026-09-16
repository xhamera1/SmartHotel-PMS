# pms-core

PMS core backend — Java 21 · Spring Boot 3.4 · Maven.

Owns reservations, rooms, room types, guests, staff authentication (JWT), and the
rate calendar (precomputed prices with manual-override precedence). Owns the `pms`
PostgreSQL schema via Flyway. Talks to `pricing-service` through a resilient internal
REST client (Resilience4j) — never on the guest booking path.

## Layout (package-by-feature, ADR-0013)

| Package | Responsibility |
|---------|----------------|
| `pl.smarthotel.pms.common` | Config, shared web utilities, global exception handling |
| `pl.smarthotel.pms.rooms` | Room types and physical rooms |
| `pl.smarthotel.pms.guests` | Guest records |
| `pl.smarthotel.pms.reservations` | Availability, booking lifecycle, state machine |
| `pl.smarthotel.pms.ratecalendar` | BAR calendar reads/overrides (pricing seam) |
| `pl.smarthotel.pms.auth` | Staff JWT login and roles |

Database:

- `src/main/resources/db/migration/V1__baseline.sql` — schema (next migration **V3**).
- `src/main/resources/db/seed/V2__seed_reference_data.sql` — dev/test seeds only.

Profiles:

| Profile | Database | Flyway locations |
|---------|----------|------------------|
| `dev` (default) | Compose Postgres (`.env`) | `migration` + `seed` |
| `test` | Testcontainers (tests) | `migration` + `seed` |
| `prod` | Env `PMS_DB_*` | `migration` only |

Hibernate `ddl-auto=validate` — Flyway owns the schema (ADR-0008).

## Run locally

From the repository root (requires JDK 21, Docker for Postgres):

```text
task up
task run:pms
```

Then open http://localhost:8080/swagger-ui.html and http://localhost:8080/actuator/health.

If you previously applied SQL via `task seed` without Flyway history, run `task db-reset`
once before the first Spring Boot start.

Environment variables: `PMS_DB_URL`, `PMS_DB_USER`, `PMS_DB_PASSWORD`, `PMS_PORT` — see
`.env.example`.

## Tests

```text
task test:java
```

- `PmsMigrationIT` / `ReservationConstraintsIT` — JDBC + Flyway constraint tests.
- `PmsCoreApplicationIT` — Spring Boot context, Flyway, actuator health on Testcontainers.

ERD: `docs/diagrams/erd-pms.md` · state machine: `docs/diagrams/reservation-state-machine.md`
· API contract: `docs/api/pms-api.md`.
