# Architecture Decision Records (ADRs)

Numbered, immutable records of architectural decisions (MADR-style, see
[`template.md`](template.md)). A superseded decision gets a new ADR that references
the old one — history is never rewritten.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-postgresql-over-mysql.md) | PostgreSQL 17 over MySQL | Accepted |
| [0002](0002-single-instance-two-schemas.md) | One PostgreSQL instance, two isolated schemas | Accepted |
| [0003](0003-two-backend-services.md) | Two backend services; event intelligence inside pricing-service | Accepted |
| [0004](0004-monorepo.md) | Monorepo | Accepted |
| [0005](0005-synchronous-rest-no-broker.md) | Synchronous REST between services; no message broker | Accepted |
| [0006](0006-precomputed-rate-calendar.md) | Precomputed rate calendar with fallback chain | Accepted |
| [0007](0007-rate-plans-derived-from-bar.md) | Rate plans as static derived rates off the ML-priced BAR | Accepted |
| [0008](0008-flyway-alembic-validate-only.md) | Flyway for pms, Alembic for pricing, ORM validate-only | Accepted |
| [0009](0009-pln-krakow-europe-warsaw.md) | PLN, Kraków location, Europe/Warsaw business time | Accepted |
| [0010](0010-ml-target-price-multiplier.md) | ML target is the revenue-optimal price multiplier | Accepted |
| [0011](0011-gemini-structured-scores-fallback.md) | Gemini structured event scores with heuristic fallback | Accepted |
| [0012](0012-jwt-staff-auth-guest-checkout.md) | Staff JWT auth; guests book without accounts | Accepted |
| [0013](0013-package-by-feature.md) | Package-by-feature in pms-core (no full hexagonal) | Accepted |

Upcoming (created together with the work they govern): event provider abstraction,
contract-testing approach.

## Creating a new ADR

1. Copy `template.md` to `NNNN-short-title.md` (next number, kebab-case title).
2. Fill it in; keep it under ~50 lines.
3. Add it to the index above and commit it together with the change it governs.
