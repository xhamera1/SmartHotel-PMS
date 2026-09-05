# ADR-0013: Package-by-feature in pms-core (no full hexagonal)

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Patryk Chamera
- **Plan reference:** Phase 2 conventions

## Context and Problem Statement

The Spring Boot service needs a package layout that stays navigable as features
grow (rooms, guests, reservations, rate calendar, auth) without over-engineering
a portfolio-sized architecture for a bachelor’s thesis.

## Considered Options

1. Global layers only (`controller` / `service` / `repository` across the app)
2. Full hexagonal / ports-and-adapters
3. **Package-by-feature** with thin shared `common` (DTOs stay per feature)

## Decision Outcome

**Chosen option:** package-by-feature, e.g. `rooms`, `guests`, `reservations`,
`ratecalendar`, `auth`, `common`. Each feature holds its controller, service,
repository, and DTOs. No full hexagonal ports/adapters layer. Cross-cutting
concerns (ProblemDetail advice, security, correlation ID, Clock) live in
`common` or Spring config.

### Consequences

- Good: changes to a reservation flow stay in one package; matches feature-based
  ownership for tests.
- Bad / risk: some duplication of patterns across features — acceptable at this
  size; extract only when a third copy appears.

## More Information

Phase 2 scaffold. Related: ADR-0012 (auth package).
