# pricing-service API — contract design

Design-time contract for the pricing microservice (FastAPI). The machine-readable
source of truth becomes the FastAPI-generated `openapi.json` exported and
drift-checked by CI (D19) once the service is scaffolded (Phase 6).

**Internal-only API**: consumed exclusively by `pms-core` (and operators). Never
exposed to browsers; not on the guest booking path (D6 — the PMS reads
precomputed prices from its rate calendar).

## Conventions

| Concern | Decision |
|---|---|
| Base path | `/api/v1` (health and operational triggers outside: `/health/*`, `/internal/*`) |
| Auth | `X-Internal-Api-Key` header on all non-health endpoints; constant-time comparison; 401 on missing/wrong |
| Payloads | JSON, camelCase; strict validation (`extra="forbid"`) — unknown fields are rejected, not ignored |
| Hotel-night dates | plain ISO `YYYY-MM-DD` |
| Money | decimal numbers, 2 fraction digits, PLN |
| Errors | RFC 7807 `application/problem+json`, mirroring the PMS convention |
| Correlation | `X-Request-ID` accepted/generated, logged, echoed |
| Design style | batch-first: one call prices a whole calendar refresh chunk |

## Endpoint inventory

| Method & path | Purpose |
|---|---|
| `POST /api/v1/quotes` | Batch price recommendations (≤ 400 items per call) |
| `GET /api/v1/demand-indicators?from&to` | DemandIndicator per night (admin proxy) |
| `GET /api/v1/events?from&to` | Scored events with impact + rationale (admin proxy) |
| `GET /api/v1/model` | Active model: version, metrics, `trainedAt` (admin UI) |
| `POST /internal/model/reload` | Operational: hot-swap to the active registry model |
| `POST /internal/events/sync` | Operational: trigger event fetch + scoring pipeline |
| `GET /health/live` | Liveness (process up) |
| `GET /health/ready` | Readiness = model loaded **and** DB reachable; compose healthchecks and integration tests rely on it |

## Canonical payloads — `POST /api/v1/quotes`

Request:

```json
{
  "requestId": "9f1c2b7e-4a10-4e0f-b1de-3f6f2a8b9c01",
  "currency": "PLN",
  "items": [
    { "roomTypeCode": "DLX", "date": "2026-09-12", "basePrice": 420.00,
      "minPrice": 300.00, "maxPrice": 800.00,
      "occupancyRate": 0.83, "roomsRemaining": 2, "leadTimeDays": 37 }
  ]
}
```

Response `200`:

```json
{
  "modelVersion": "rf-20260801-a3f2",
  "items": [
    { "roomTypeCode": "DLX", "date": "2026-09-12",
      "price": 612.00, "multiplier": 1.457, "demandIndicator": 78,
      "factors": { "demandIndicator": 78, "majorEvent": true, "weekend": true,
                   "occupancyRate": 0.83,
                   "topSignals": ["demand_indicator", "occupancy_rate", "is_weekend"] } }
  ]
}
```

Semantics:

- `price` is the recommended **BAR**, already clamped to `[minPrice, maxPrice]`
  and rounded to whole PLN; `multiplier = price / basePrice` before rounding.
- `factors` is the explanation payload (JSONB-ready): the PMS persists it into
  `rate_calendar.factors`, the admin UI renders it ("why is this price high?").
- Every response item is also written to `prediction_log` via a background task
  (never blocks the response).
- The caller (PMS) supplies occupancy/lead-time features — the pricing service
  does not read the `pms` schema (ADR-0002).

## Error contract

| Case | Response |
|---|---|
| Missing/wrong `X-Internal-Api-Key` | `401` problem+json |
| Validation error (unknown field, > 400 items, malformed date, min > max) | `422` problem+json with `errors[]` |
| Model not loaded (startup, failed reload) | `503`; `/health/ready` reports not-ready — callers must fall back (`BASE_FALLBACK`) |
| Unexpected server error | `500` problem+json, correlation ID included; details stay in logs |

## Resilience contract with pms-core (client side, Phase 8)

Connect timeout 1 s · read timeout 3 s (10 s batch) · ≤ 2 retries with jittered
exponential backoff on 5xx/timeouts · circuit breaker (window 10, open at 50 %,
half-open after 30 s) · on any final failure the PMS uses base prices marked
`BASE_FALLBACK` — bookings never fail because pricing is down (D6).

## Contract governance

- Phase 6 CI exports `openapi.json` and fails on drift vs. the committed copy;
  schemathesis fuzzes the live contract.
- Phase 8 adds consumer-driven contract tests (PMS WireMock stubs generated from
  this contract) — a change here without updating the stubs breaks CI by design.
