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

Upcoming (created when their phase lands — see plan Appendix D): 0007 ML target
variable (Phase 4/5), 0008 event provider abstraction (Phase 7), 0009 Gemini
integration design (Phase 7), 0010 auth model (Phase 2), 0011 layered
package-by-feature (Phase 2), 0012 contract-testing approach (Phase 6/8).

## Creating a new ADR

1. Copy `template.md` to `NNNN-short-title.md` (next number, kebab-case title).
2. Fill it in; keep it under ~50 lines — link to the plan for details.
3. Add it to the index above and land it via PR together with the change it governs.
