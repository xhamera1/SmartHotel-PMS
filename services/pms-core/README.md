# pms-core

PMS core backend — Java 21 · Spring Boot 3.4 · Maven.

Owns reservations, rooms, room types, guests, staff authentication (JWT), and the
rate calendar (precomputed prices with manual-override precedence). Owns the `pms`
PostgreSQL schema via Flyway. Talks to `pricing-service` through a resilient internal
REST client (Resilience4j) — never on the guest booking path.

## Layout (package-by-feature, ADR-0013)

| Package | Responsibility |
|---------|----------------|
| `pl.smarthotel.pms.common` | Config, ProblemDetail advice, correlation ID, MapStruct, audited entities |
| `pl.smarthotel.pms.rooms` | Room types and physical rooms |
| `pl.smarthotel.pms.guests` | Guest records; email dedup for booking |
| `pl.smarthotel.pms.reservations` | Availability, booking lifecycle, state machine, night audit |
| `pl.smarthotel.pms.ratecalendar` | BAR calendar + `PriceProvider` seam + admin overrides (ADR-0006) |
| `pl.smarthotel.pms.dashboard` | Front-desk KPIs |
| `pl.smarthotel.pms.auth` | Staff JWT login and roles |

### API conventions (Phase 2 step 2)

- Request/response DTOs are Java **`record`s**; MapStruct maps entities ↔ DTOs (no entity leakage).
- Bean Validation on request bodies; failures → RFC 7807 `application/problem+json`.
- `X-Request-ID` accepted or generated, stored in MDC, echoed on every response.
- JPA auditing (`created_at` / `updated_at`) via `AuditedEntity`; optimistic lock via `VersionedAuditedEntity`.
- Injectable `Clock` (UTC) and hotel `ZoneId` (`Europe/Warsaw`) — never call `Instant.now()` ad hoc.

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
docker compose --env-file .env -f infra/compose.yml --profile core up -d --wait
cd services\pms-core
.\mvnw.cmd -B -ntp spring-boot:run "-Dspring-boot.run.profiles=dev"
```

Then open:

- http://localhost:8080/swagger-ui — OpenAPI UI (Authorize with Bearer JWT)
- http://localhost:8080/v3/api-docs — OpenAPI JSON
- http://localhost:8080/actuator/health — overall health
- http://localhost:8080/actuator/health/readiness — DB-ready probe (compose / k6)
- http://localhost:8080/actuator/info — app name/version

Environment variables: `PMS_DB_URL`, `PMS_DB_USER`, `PMS_DB_PASSWORD`, `PMS_PORT`,
`JWT_SECRET` (at least 32 chars), `CORS_ALLOWED_ORIGINS` — see `.env.example`.

## Auth (ADR-0012)

| Method | Path | Notes |
|--------|------|--------|
| POST | `/api/v1/auth/login` | email + password → access (~60 min) + refresh (~24 h); BCrypt; bucket4j rate limit |
| POST | `/api/v1/auth/refresh` | refresh token → new access/refresh pair |

**Roles:** `ADMIN`, `RECEPTIONIST`. Dev seeds: `admin@smarthotel.local` / `admin-dev-password`,
`reception@smarthotel.local` / `reception-dev-password`.

## Tests & quality gates

```text
cd services\pms-core
.\mvnw.cmd -B -ntp verify
```

Runs unit + Testcontainers ITs, Checkstyle, SpotBugs (High), ArchUnit, and JaCoCo ≥ 80% on
service/domain packages. CI job: `backend-java (pms-core)`.

## Public & admin API (Phase 2)

| Method | Path | Auth | Notes |
|--------|------|------|--------|
| GET | `/api/v1/availability` | public | Inventory + BAR + rate-plan totals |
| POST | `/api/v1/reservations` | public | Guest checkout |
| GET | `/api/v1/reservations/lookup` | public | By code + email |
| POST | `/api/v1/reservations/{code}/cancel` | public | Guest cancel |
| GET/POST | `/api/v1/admin/reservations` | JWT | List/filter + walk-in |
| POST | `/api/v1/admin/reservations/{id}/check-in\|check-out\|cancel\|no-show` | JWT | Staff transitions |
| GET | `/api/v1/admin/rate-calendar` | JWT | Calendar view |
| PUT/DELETE | `/api/v1/admin/rate-calendar/{roomTypeCode}/{date}` | JWT `ADMIN` | Manual override |
| GET | `/api/v1/admin/dashboard/kpis` | JWT | Occupancy / arrivals / MTD revenue |
| GET | `/api/v1/admin/rate-plans` | JWT | Active rate-plan catalog |
| GET/POST/… | `/api/v1/admin/room-types` · `/rooms` · `/guests` | JWT | Catalogue CRUD |

ERD: `docs/diagrams/erd-pms.md` · API contract: `docs/api/pms-api.md`.
