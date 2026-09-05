# ADR-0003: Two backend services; event intelligence inside pricing-service

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Patryk Chamera
- **Plan reference:** D3, §3.2

## Context and Problem Statement

The thesis mandates a microservices architecture with the pricing module as an
independently developed and tested component (§2.1), while listing "Integration
with LLM" as a separate functional area (§2.3). Where should event ingestion and
Gemini scoring live, and how many deployables should a solo developer operate?

## Considered Options

1. Modular monolith (single Spring Boot app)
2. Two services: `pms-core` (Java) + `pricing-service` (Python) with event
   intelligence as an internal module of the pricing service
3. Three services: separate event-intelligence microservice

## Decision Outcome

**Chosen option:** two services. Events exist solely to produce pricing features
(the demand indicator), so they are cohesive with the pricing domain; ML serving
and scikit-learn require Python anyway. Option 1 would violate the thesis's
architectural mandate; option 3 doubles Python operational surface (deploy,
observability, CI) with no additional thesis value.

Inside `pricing-service`, `events/` and `ml/` are separate packages that do not
import each other's internals — they share only the `daily_demand` table and typed
interfaces, keeping a documented extraction seam if a third service is ever argued.

### Consequences

- Good: one deployable per language; clear ownership; independent testability.
- Good: extraction seam preserved and documented (thesis design-chapter material).
- Bad / risk: pricing-service accumulates several responsibilities — mitigated by
  strict internal package boundaries and per-package test suites.

## More Information

Plan §3.2 and Phases 4–7. Related: ADR-0004 (monorepo), ADR-0005 (communication).
