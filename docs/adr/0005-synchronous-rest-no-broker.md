# ADR-0005: Synchronous REST between services; no message broker

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Patryk Chamera
- **Plan reference:** D5, §3.3

## Context and Problem Statement

`pms-core` (Java) must obtain price recommendations from `pricing-service`
(Python). The protocol is unspecified in the thesis description. Requirements:
testability with the chosen QA stack, resilience to the pricing service being
down, demo-friendliness, and effort proportional to a single-hotel scale.

## Considered Options

1. Synchronous REST/JSON with OpenAPI contract and client-side resilience
2. gRPC
3. Asynchronous messaging (RabbitMQ/Kafka)

## Decision Outcome

**Chosen option:** synchronous REST/JSON. Batch-first endpoints (one call prices up
to ~366 room-nights) amortize HTTP overhead; the Java client wraps calls in
Resilience4j (timeouts, retry ×2 with jittered backoff, circuit breaker) with a
fallback to base prices; requests carry `X-Internal-Api-Key` and the pricing
service is not exposed outside the Docker network. The generated OpenAPI spec is a
committed artifact with CI drift gates (contract testing, D19).

gRPC rejected: tooling friction across the QA stack (RestAssured, WireMock,
schemathesis) with no performance need. Broker rejected: a nightly batch plus
occasional on-demand quotes have no throughput/decoupling requirement that
justifies operating Kafka/RabbitMQ; noted as future work for multi-property
fan-out.

### Consequences

- Good: human-debuggable, stub-able, fuzz-able; every tool in the QA plan applies.
- Bad / risk: temporal coupling to pricing-service availability — mitigated by
  the precomputed rate calendar and fallback chain (ADR-0006).

## More Information

Plan §3.3; failure-mode table in plan Phase 8.
