# pms-core API — contract design

Design-time contract for the PMS core backend (Spring Boot). The machine-readable
source of truth becomes the springdoc-generated OpenAPI spec exported by CI once
the service is scaffolded; until then this document *is* the contract, and
endpoint changes land here first.

## Conventions (apply to every endpoint)

| Concern | Decision |
|---|---|
| Base path | `/api/v1` (URI versioning; breaking changes → `/api/v2`) |
| Payloads | JSON, camelCase properties |
| Hotel-night dates | plain ISO `YYYY-MM-DD` strings, hotel-local (Europe/Warsaw) |
| Timestamps | ISO-8601 with offset, UTC (`2026-09-05T12:00:00Z`) |
| Money | decimal number with 2 fraction digits + separate `currency` (`PLN` only) |
| Errors | RFC 7807 `application/problem+json`; `type` identifies the error class |
| Pagination | `?page=0&size=20` (cursor-less); response wraps `content` + `page` metadata |
| Correlation | `X-Request-ID` accepted or generated; always echoed back |
| Auth (staff) | `Authorization: Bearer <JWT>` — HS256, access ~60 min, refresh ~24 h |
| Auth (public) | none; booking access via confirmation code + email pair |
| Roles | `ADMIN` (full), `RECEPTIONIST` (operational: reservations, guests, calendar view) |

## Endpoint inventory

### Public (no auth)

| Method & path | Purpose | Phase |
|---|---|---|
| `GET /api/v1/availability?checkIn&checkOut&guests` | Available room types for a Stay with per-rate-plan prices | 2 |
| `POST /api/v1/reservations` | Guest-checkout booking | 2 |
| `GET /api/v1/reservations/lookup?code&email` | Reservation details by confirmation code + email | 2 |
| `POST /api/v1/reservations/{code}/cancel` | Guest cancellation (refundable rate plans only) | 2 |

### Auth

| Method & path | Purpose | Phase |
|---|---|---|
| `POST /api/v1/auth/login` | email + password → access/refresh tokens | 2 |
| `POST /api/v1/auth/refresh` | refresh token → new access token | 2 |

### Admin (JWT; role in parentheses)

| Method & path | Purpose | Phase |
|---|---|---|
| `GET/POST /api/v1/admin/room-types` · `GET/PUT/DELETE /api/v1/admin/room-types/{id}` | Room-type management (ADMIN); delete → `409` when active reservations exist | 2 |
| `GET/POST /api/v1/admin/rooms` · `GET/PUT /api/v1/admin/rooms/{id}` | Room management incl. `status` (ADMIN) | 2 |
| `GET /api/v1/admin/rate-plans` | Rate-plan catalog (both roles; managed via seeds for now, ADR-0007) | 2 |
| `GET /api/v1/admin/guests?query&page&size` | Guest search by name/email (both roles) | 2 |
| `GET /api/v1/admin/reservations?status&from&to&query&page&size` | Reservation list/filter (both roles) | 2 |
| `POST /api/v1/admin/reservations` | Walk-in/phone booking (`source=ADMIN`) | 2 |
| `POST /api/v1/admin/reservations/{id}/check-in` · `/check-out` · `/cancel` · `/no-show` | State transitions (both roles; see state machine) | 2 |
| `GET /api/v1/admin/rate-calendar?roomTypeCode&from&to` | Calendar view: BAR + source + demand indicator (both roles) | 2 |
| `PUT /api/v1/admin/rate-calendar/{roomTypeCode}/{date}` | Manual price override → `source=MANUAL` (ADMIN) | 2 |
| `DELETE /api/v1/admin/rate-calendar/{roomTypeCode}/{date}` | Remove manual override (ADMIN) | 2 |
| `GET /api/v1/admin/dashboard/kpis` | Occupancy today, arrivals/departures, MTD revenue (both roles) | 2 |
| `POST /api/v1/admin/pricing/refresh` | Trigger rate-calendar refresh via pricing service (ADMIN) | 8 |
| `GET /api/v1/admin/pricing/demand-indicators?from&to` · `/events?from&to` · `/model` | Proxies to the pricing service for the admin UI (both roles) | 8 |

## Canonical payloads

### `GET /api/v1/availability?checkIn=2026-10-03&checkOut=2026-10-05&guests=2` → `200`

```json
{
  "checkIn": "2026-10-03",
  "checkOut": "2026-10-05",
  "guests": 2,
  "currency": "PLN",
  "roomTypes": [
    {
      "code": "DLX",
      "name": "Deluxe Double",
      "capacity": 3,
      "roomsLeft": 2,
      "nights": [
        { "date": "2026-10-03", "bar": 612.00, "priceSource": "ML_MODEL" },
        { "date": "2026-10-04", "bar": 580.00, "priceSource": "ML_MODEL" }
      ],
      "ratePlans": [
        { "code": "NONREF", "name": "Non-refundable", "refundable": false,
          "breakfastIncluded": false, "totalPrice": 1072.80 },
        { "code": "FLEX", "name": "Flexible", "refundable": true,
          "breakfastIncluded": false, "totalPrice": 1192.00 },
        { "code": "BB", "name": "Bed & Breakfast", "refundable": true,
          "breakfastIncluded": true, "totalPrice": 1370.80 }
      ]
    }
  ]
}
```

Notes: `bar` is the nightly Best Available Rate from the rate calendar (fallback:
room-type `basePrice` with `priceSource=BASE`); rate-plan totals are
`Σ(bar × priceModifier)` rounded per night to grosz.

### `POST /api/v1/reservations` → `201`

Request:

```json
{
  "roomTypeCode": "DLX",
  "ratePlanCode": "NONREF",
  "checkIn": "2026-10-03",
  "checkOut": "2026-10-05",
  "adults": 2,
  "guest": {
    "firstName": "Jan", "lastName": "Kowalski",
    "email": "jan.kowalski@example.com", "phone": "+48 600 100 200"
  }
}
```

Response (`Location: /api/v1/reservations/lookup?code=K7NR4PWM&email=…`):

```json
{
  "confirmationCode": "K7NR4PWM",
  "status": "CONFIRMED",
  "roomType": "DLX",
  "ratePlan": { "code": "NONREF", "refundable": false, "breakfastIncluded": false },
  "checkIn": "2026-10-03",
  "checkOut": "2026-10-05",
  "adults": 2,
  "totalPrice": 1072.80,
  "currency": "PLN",
  "priceBreakdown": [
    { "date": "2026-10-03", "price": 550.80, "barPrice": 612.00, "priceSource": "ML_MODEL" },
    { "date": "2026-10-04", "price": 522.00, "barPrice": 580.00, "priceSource": "ML_MODEL" }
  ]
}
```

### Error catalog — RFC 7807

All errors use `Content-Type: application/problem+json` with a stable `type` URI under
`https://smarthotel/problems/…` (Java source of truth: `ProblemTypes`).

| `type` suffix | HTTP | When |
|---|---|---|
| `/validation-error` | 400 (405 for wrong method) | Bean Validation, malformed JSON, missing/invalid query params |
| `/unauthorized` | 401 | Bad login, missing/invalid/expired JWT, refresh token used as access |
| `/forbidden` | 403 | Authenticated but role insufficient (`@PreAuthorize`) |
| `/not-found` | 404 | Unknown resource / unknown route |
| `/conflict` | 409 | Generic business conflict (e.g. duplicate email or room code) |
| `/room-no-longer-available` | 409 | Inventory race / exclusion constraint |
| `/rate-plan-not-refundable` | 409 | Guest cancel blocked by rate plan |
| `/illegal-state-transition` | 409 | Reservation state-machine rejection |
| `/rate-limited` | 429 | Login rate limit (bucket4j) |
| `/internal-error` | 500 | Unexpected failure |

Every problem includes `title`, `status`, `detail`, `instance` (request path), and echoes
`X-Request-ID` as `requestId` when present. Validation errors may add `errors: [{field, message}]`.

Room taken between availability view and booking (`409`):

```json
{
  "type": "https://smarthotel/problems/room-no-longer-available",
  "title": "Room no longer available",
  "status": 409,
  "detail": "No DLX room is free for 2026-10-03 – 2026-10-05 anymore.",
  "instance": "/api/v1/reservations"
}
```

Guest cancelling a non-refundable booking (`409`, distinct type — the frontend
must explain *why*):

```json
{
  "type": "https://smarthotel/problems/rate-plan-not-refundable",
  "title": "Rate plan is not refundable",
  "status": 409,
  "detail": "Reservation K7NR4PWM uses the NONREF rate and cannot be cancelled online.",
  "instance": "/api/v1/reservations/K7NR4PWM/cancel"
}
```

## Contract governance

- Phase 2 exports `openapi.json` from springdoc in CI and fails on drift vs. the
  committed copy (D19); this document then shrinks to conventions + rationale.
- Live UI: `/swagger-ui` · machine-readable: `/v3/api-docs`.
- Contract changes require: update here (or OpenAPI) + consumer test update in
  the same commit.
