# ADR-0006: Precomputed rate calendar with fallback chain

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Patryk Chamera
- **Plan reference:** D6, §3.4

## Context and Problem Statement

How do ML-recommended prices reach guests? Calling the pricing service
synchronously during availability search / booking would put an external ML call
on the guest-facing critical path — latency, availability coupling, and load
amplification.

## Considered Options

1. Synchronous quote call on every guest request
2. Precomputed `rate_calendar` refreshed nightly + manual trigger (with fallbacks)
3. Event-driven price push from the pricing service

## Decision Outcome

**Chosen option:** precomputed `pms.rate_calendar`. A scheduled job (03:00
Europe/Warsaw) sends occupancy features to the pricing service in chunks and
upserts recommended prices for the next 180 days; an admin "Refresh now" button
triggers the same logic. Rules: manual overrides (`source=MANUAL`) always win and
are never overwritten; model output is clamped to per-room-type `[min, max]`
guardrails; on a calendar miss the PMS attempts one short on-demand quote, then
falls back to `base_price` with an explicit source flag. The guest booking path
reads only the calendar — it never blocks on the ML service.

### Consequences

- Good: guest-facing latency and availability are independent of the pricing
  service — enabling the flagship resilience demo (kill pricing, bookings still work).
- Good: every reservation snapshots its `price_breakdown` — full auditability.
- Bad / risk: prices can be up to ~24 h stale — acceptable for the domain;
  mitigated by the manual refresh trigger.

## More Information

Plan §3.4 and Phase 8. Related: ADR-0005.
