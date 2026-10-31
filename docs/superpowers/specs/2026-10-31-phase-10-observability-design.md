# Phase 10 — Observability Design

**Date:** 2026-10-31  
**Status:** approved for implementation (locked to `detailed_implementation_plan.md` Phase 10 + user request to plan then implement)

## Goal

Every request is traceable across frontend → PMS → pricing; logs are JSON-searchable in Elasticsearch; Kibana dashboards support ops and thesis telemetry.

## Current baseline (reuse)

| Piece | Status |
|-------|--------|
| Compose `observability` profile (ES 1g, Kibana, Filebeat) | MVP exists |
| Nightly `elk-smoke` (`_count > 0`) | Placeholder exists |
| FE `X-Request-ID` per axios call | Done |
| PMS `CorrelationIdFilter` → MDC `requestId` | Done |
| Pricing `CorrelationIdMiddleware` | Done (state only, not in logs) |
| logstash-logback-encoder / structlog | **Missing** |
| Shared field schema + PII mask | **Missing** |
| Business event logs | **Missing** |
| RestClient forwards `X-Request-ID` | **Missing** |
| ILM 7d + `dynamic: false` template | **Missing** |
| Kibana ndjson | **Missing** |

## Design decisions

1. **Correlation field:** keep HTTP header / Problem Details as `X-Request-ID` / `requestId`; also put the same value in MDC / structlog as **`traceId`** (plan schema).
2. **JSON only in containers:** Spring profile `docker` (and prod) → LogstashEncoder stdout; local `dev` stays human-readable. Python always JSON on stdout in docker; pytest may use console.
3. **HTTP access log:** one structured INFO line per request with `http.method`, `http.path`, `http.status`, `durationMs` (exclude actuator/health noise if cheap).
4. **Business events:** dedicated logger / `event=` field — `PricingDecisionMade`, `ReservationCreated`, `ReservationCancelled`, `GeminiCallCompleted`. No guest emails in cleartext (mask).
5. **Propagation:** RestClient interceptor copies MDC `traceId`/`requestId` → `X-Request-ID` on every pricing call (including async `supplyAsync` — capture ID on calling thread before async).
6. **ES mapping:** committed index template `dynamic: false` + ILM delete @ 7d; Filebeat ships to `smarthotel-*`.
7. **Kibana:** hand-authored ndjson (data view, 4 saved searches, 2 dashboards) imported via script; not exported from a live UI dependency.
8. **CI:** schema/PII unit tests in java/python jobs; ELK smoke stays **nightly only**; extend smoke to assert `_count > 0` and optionally documents with a planted `traceId`.

## Out of scope

- Full distributed APM / OpenTelemetry collectors  
- Logstash  
- Making ELK required on PR  
- Perfect Lens visualizations (markdown + saved-search based dashboards OK for thesis)

## Exit criteria (definition of done)

- [x] Same `traceId` in PMS + pricing logs for one proxied request (WireMock header + middleware context + smoke plant)  
- [x] PII mask unit-tested both stacks  
- [x] Business events emitted at least once on happy paths  
- [x] `infra/elk/*.ndjson` + template + ILM committed  
- [x] Nightly elk-smoke green path documented; current-status Phase 10 updated  
