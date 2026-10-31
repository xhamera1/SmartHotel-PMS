# Observability design (Phase 10)

## Purpose

Make every guest/staff action reconstructible across the SPA, `pms-core`, and `pricing-service`, and provide searchable telemetry for thesis evaluation (pricing decisions, Gemini outcomes, reservation lifecycle) without storing PII in cleartext.

## Correlation model

```
Browser (axios)                PMS                          Pricing
───────────────                ───                          ───────
X-Request-ID: <uuid>  ──►  MDC requestId=traceId=<uuid>
                           RestClient header  ──────────►  request.state.request_id
                                                              structlog contextvars
                                                              traceId=<uuid>
```

- HTTP header and Problem Details field: `X-Request-ID` / `requestId` (unchanged API).  
- Shared log field: **`traceId`** (same value).  
- Async pricing calls capture the id **before** `CompletableFuture.supplyAsync` so MDC is not lost.

## Log schema (stdout JSON)

| Field | Meaning |
|-------|---------|
| `@timestamp` | Event time (ISO) |
| `level` | INFO / WARN / ERROR |
| `service` | `pms-core` or `pricing-service` |
| `traceId` | Correlation id |
| `message` | Short text / event name |
| `http.method` / `http.path` / `http.status` | Access log |
| `durationMs` | Request latency |
| `businessEvent` | Business event name when applicable |

**Business events:** `PricingDecisionMade`, `ReservationCreated`, `ReservationCancelled`, `GeminiCallCompleted`.

**PII:** emails masked via `PiiMasker` / `mask_email` (`a***@domain`).

## Stack

Compose profile **`observability`** only (RAM gate):

- Elasticsearch 8.17 single-node, `ES_JAVA_OPTS=-Xms1g -Xmx1g`
- Kibana 5601
- Filebeat Docker autodiscover → index `smarthotel-yyyy.MM.dd`
- ILM policy `smarthotel-7d` (delete after 7 days)
- Index template `dynamic: false` — fixed field set to avoid mapping explosion

## Kibana (committed ndjson)

- Data view `smarthotel-*`
- Searches: errors by service, slow >1s, fallback pricing, Gemini failures
- Dashboards: **Ops Overview**, **Pricing Analytics** (markdown + Discover workflow; Lens optional later)

Import: `bash infra/elk/import-kibana.sh` (tworzy Data View przez API z `timeFieldName=@timestamp` — ręczny ndjson `index-pattern` psuje Discover w 8.17).

## Ops workflow (exit criterion)

1. Open an error in Kibana.  
2. Copy `traceId`.  
3. Filter Discover: `traceId:"…"`.  
4. Confirm both `service:pms-core` and `service:pricing-service` lines when the request crossed the pricing client.

## Verified walkthrough (2026-10-31) — book + cancel

**Verdict:** OK — end-to-end guest booking and guest cancel appear in Kibana Discover as structured logs with matching `confirmationCode` / `traceId` per HTTP call.

**Setup used:** compose profiles `app` + `observability`, Data View **SmartHotel logs** (`smarthotel-*`, time field `@timestamp`), UI http://localhost:8088, Kibana http://localhost:5601 (Last 15 minutes).

**Action:** guest booked room type `DLX`, confirmation `X5TW36R6`, then cancelled online.

**Discover timeline** (index `smarthotel-2026.10.31`, `service:pms-core`):

| Local time | `businessEvent` / access | Key fields |
|------------|--------------------------|------------|
| 16:27:15 | `GET /api/v1/availability` 200 | `durationMs:28`, `traceId:a3aabf7d-…` |
| 16:27:37 | **`ReservationCreated`** | `confirmationCode:X5TW36R6`, `roomType:DLX`, `source:WEB`, `traceId:42b99161-c768-4397-beea-4def1cb1f219` |
| 16:27:37 | `POST /api/v1/reservations` **201** | same `traceId` as Created (`durationMs:362`) |
| 16:28:28 | `GET /api/v1/reservations/lookup` 200 | new `traceId` (new axios call) |
| 16:28:31 | **`ReservationCancelled`** | `confirmationCode:X5TW36R6`, `actor:guest`, `traceId:16a9ff25-1648-4415-982e-368debb47be5` |
| 16:28:31 | `POST /api/v1/reservations/X5TW36R6/cancel` **200** | same `traceId` as Cancelled |

**How to reproduce the filter in Discover:**

```kql
confirmationCode:"X5TW36R6"
```

or one request trail:

```kql
traceId:"42b99161-c768-4397-beea-4def1cb1f219"
```

**Notes for the thesis**

- Create and cancel use **different** `traceId` values by design (SPA attaches a fresh `X-Request-ID` per HTTP request).  
- Within one request, access log + business event share the same `traceId` (Created↔201, Cancelled↔cancel 200).  
- Lifecycle across calls is joined by `confirmationCode` (or guest email is **not** logged in cleartext).  
- Field name is `businessEvent` (not ECS `event`) to avoid Filebeat/ES mapping clashes.

## Load-test note

Under k6 (Phase 11), keep INFO sampling or rely on ILM; do not raise root log level to DEBUG in the observability profile.

