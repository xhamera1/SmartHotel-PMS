# pms-core

PMS core backend — Java 21 · Spring Boot · Maven.

Owns reservations, rooms, room types, guests, staff authentication (JWT), and the
rate calendar (precomputed prices with manual-override precedence). Owns the `pms`
PostgreSQL schema via Flyway. Talks to `pricing-service` through a resilient internal
REST client (Resilience4j) — never on the guest booking path.

The Spring Boot skeleton is not scaffolded yet, but the `pms` schema DDL already
lives here — `src/main/resources/db/migration/V1__baseline.sql` (Flyway) — so the
scaffold picks it up unchanged. ERD: `docs/diagrams/erd-pms.md`.
