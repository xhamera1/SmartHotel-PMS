# pms-core

PMS core backend — Java 21 · Spring Boot · Maven.

Owns reservations, rooms, room types, guests, staff authentication (JWT), and the
rate calendar (precomputed prices with manual-override precedence). Owns the `pms`
PostgreSQL schema via Flyway. Talks to `pricing-service` through a resilient internal
REST client (Resilience4j) — never on the guest booking path.

The Spring Boot skeleton is not scaffolded yet, but the database artifacts already
live here and the scaffold picks them up unchanged:

- `src/main/resources/db/migration/V1__baseline.sql` — `pms` schema (Flyway; next
  schema migration starts at **V3**).
- `src/main/resources/db/seed/V2__seed_reference_data.sql` — dev/test seeds
  (rate plans, room types, 35 rooms, staff users); the dev/test Spring profiles
  add `classpath:db/seed` to `spring.flyway.locations`, prod does not.

ERD: `docs/diagrams/erd-pms.md` · state machine: `docs/diagrams/reservation-state-machine.md`
· API contract: `docs/api/pms-api.md`.
