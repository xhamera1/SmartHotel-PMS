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
| `pl.smarthotel.pms.ratecalendar` | BAR calendar + `PriceProvider` seam (ADR-0006) |
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
- http://localhost:8080/actuator/health/liveness — process liveness
- http://localhost:8080/actuator/info — app name/version

Environment variables: `PMS_DB_URL`, `PMS_DB_USER`, `PMS_DB_PASSWORD`, `PMS_PORT`,
`JWT_SECRET` (at least 32 chars), `CORS_ALLOWED_ORIGINS` — see `.env.example`.

## Auth (Phase 2 step 8, ADR-0012)

Staff JWT (HS256) via Spring Security OAuth2 resource-server. Guests stay unauthenticated
and use confirmation code + email.

| Method | Path | Notes |
|--------|------|--------|
| POST | `/api/v1/auth/login` | email + password → access (~60 min) + refresh (~24 h); BCrypt; in-memory bucket4j rate limit |
| POST | `/api/v1/auth/refresh` | refresh token → new access/refresh pair |

**Roles:** `ADMIN` (room types/rooms + everything), `RECEPTIONIST` (guests + reservation ops).
Method security via `@PreAuthorize`. CORS is locked to `app.cors.allowed-origins`.

**Dev seed users** (profile `dev`/`test` only):

- `admin@smarthotel.local` / `admin-dev-password` (`ADMIN`)
- `reception@smarthotel.local` / `reception-dev-password` (`RECEPTIONIST`)

## Ops polish (Phase 2 step 9)

- Error catalog: stable `https://smarthotel/problems/…` types (`ProblemTypes` + `docs/api/pms-api.md`)
- Actuator: only `health` + `info` exposed; probes enabled for future compose healthchecks and k6

## Tests

```text
cd services\pms-core
.\mvnw.cmd -B -ntp verify
```

- Unit: state machine, pricing, confirmation codes, exclusion-constraint translation, availability
- API IT: `PmsCoreApplicationIT` (actuator/swagger/errors), `AuthApiIT`, `AvailabilityApiIT`,
  `ReservationApiIT`, `DoubleBookingRaceIT`, rooms/guests admin ITs

## Public & admin API

| Method | Path | Auth | Notes |
|--------|------|------|--------|
| GET | `/api/v1/availability?checkIn&checkOut&guests` | public | Free inventory + BAR + rate-plan totals |
| POST | `/api/v1/reservations` | public | Guest checkout → `CONFIRMED`; assigns free room; price snapshot |
| GET | `/api/v1/reservations/lookup?code&email` | public | Lookup by confirmation code + email |
| POST | `/api/v1/reservations/{code}/cancel?email=` | public | Guest cancel (refundable, before check-in) |
| POST | `/api/v1/admin/reservations` | JWT | Walk-in (`source=ADMIN`) |
| POST | `/api/v1/admin/reservations/{id}/check-in\|check-out\|cancel` | JWT | Staff transitions |
| GET/POST | `/api/v1/admin/room-types` · `/rooms` | JWT `ADMIN` | Room catalogue |
| GET/POST | `/api/v1/admin/guests` | JWT `ADMIN`\|`RECEPTIONIST` | Guest CRUD |

**Lifecycle:** create → `CONFIRMED`; staff check-in/out; guest cancel (refundable + before
check-in) or staff cancel; night-audit job (`app.night-audit.cron`, default 00:05 Warsaw)
marks missed check-ins as `NO_SHOW`. Confirmation codes: 8-char unambiguous alphabet,
collision-checked. `price_breakdown` is snapshotted at booking.

**Concurrency:** the `no_double_booking` exclusion constraint is the last line of defense.
Violations become `RoomNoLongerAvailableException` → HTTP 409 `room-no-longer-available`
(`DoubleBookingRaceIT` asserts exactly one of two parallel bookings succeeds).

ERD: `docs/diagrams/erd-pms.md` · state machine: `docs/diagrams/reservation-state-machine.md`
· API contract: `docs/api/pms-api.md`.
