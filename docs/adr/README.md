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

Upcoming (created together with the work they govern): ML target variable, event
provider abstraction, Gemini integration design, auth model, layered
package-by-feature structure, contract-testing approach.

## Creating a new ADR

1. Copy `template.md` to `NNNN-short-title.md` (next number, kebab-case title).
2. Fill it in; keep it under ~50 lines.
3. Add it to the index above and commit it together with the change it governs.
