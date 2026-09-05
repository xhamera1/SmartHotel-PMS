# pms-core

PMS core backend — Java 21 · Spring Boot · Maven.

Owns reservations, rooms, room types, guests, staff authentication (JWT), and the
rate calendar (precomputed prices with manual-override precedence). Owns the `pms`
PostgreSQL schema via Flyway. Talks to `pricing-service` through a resilient internal
REST client (Resilience4j) — never on the guest booking path.

Scaffolded in **Phase 2** of the [implementation plan](../../docs/detailed_implementation_plan.md).
