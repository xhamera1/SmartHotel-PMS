# Phase 10 Observability Implementation Plan

> **For agentic workers:** execute task-by-task; checkboxes track progress.

**Goal:** Shared JSON log schema + business events + ELK template/ILM + Kibana ndjson + correlation end-to-end tests/smoke.

**Architecture:** Apps emit JSON stdout → Filebeat Docker autodiscover → ES `smarthotel-*` (fixed mapping, 7d ILM) → Kibana saved objects. `X-Request-ID` / `traceId` correlates FE → PMS → pricing.

**Tech Stack:** logstash-logback-encoder, structlog, Elasticsearch/Kibana/Filebeat 8.17.3

## Global Constraints

- Observability stays behind compose profile `observability`; ES heap ≤ 1g  
- No cleartext emails in logs  
- `dynamic: false` on index template  
- ELK smoke nightly-only  

---

### Task 1: Java JSON logging + PII + HTTP access + business events

**Files:**
- `services/pms-core/pom.xml` — add `net.logstash.logback:logstash-logback-encoder`
- `services/pms-core/src/main/resources/logback-spring.xml`
- `services/pms-core/src/main/java/.../common/logging/PiiMasker.java` + test
- `services/pms-core/src/main/java/.../common/logging/BusinessEvents.java`
- `services/pms-core/src/main/java/.../common/web/HttpAccessLogFilter.java`
- Update `CorrelationIdFilter` to set MDC `traceId` = same as `requestId`
- Emit events from `ReservationService` / pricing decision path (`RateCalendarPriceProvider` or upsert)

- [x] Implement + unit tests for PiiMasker / schema shape
- [x] Verify module tests for logging helpers

### Task 2: Propagate X-Request-ID on pricing RestClient

**Files:** `PricingClientConfig.java`, `PricingHttpGateway.java` (capture MDC before async)

- [x] WireMock assertion: outbound call includes `X-Request-ID`

### Task 3: Python structlog + middleware + Gemini/quote events

**Files:**
- `pyproject.toml` — `structlog`
- `app/logging_config.py`, wire in `main.py`
- Enhance `correlation.py` + HTTP middleware for duration/status
- `events/scoring/gemini.py` — `GeminiCallCompleted`
- `app/services/quoting.py` — optional `PricingDecisionMade` sample/batch summary
- `app/observability/pii.py` + tests

- [x] pytest for PII + log schema keys

### Task 4: ELK hardening

**Files:** `infra/elk/filebeat.yml`, `ilm-policy.json`, `index-template.json`, compose volume mounts, `infra/elk/setup-es.sh`, `smoke.sh`

- [x] Template + ILM applied before/with Filebeat
- [x] Smoke asserts `_count > 0`

### Task 5: Kibana ndjson + docs

**Files:** `infra/elk/kibana-saved-objects.ndjson`, README, `docs/architecture/observability.md`, current-status

- [x] Import instructions documented

### Task 6: Correlation smoke in nightly

Extend nightly elk-smoke: plant `X-Request-ID`, hit PMS health or quotes path, wait, query ES for `traceId`.

- [x] Update `nightly.yml` if script path changes
