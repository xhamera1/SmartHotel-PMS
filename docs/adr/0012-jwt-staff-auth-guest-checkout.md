# ADR-0012: Staff JWT auth; guests book without accounts

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Patryk Chamera
- **Plan reference:** Phase 2 auth design; product goals P1–P2

## Context and Problem Statement

The system has two actor classes: hotel staff (admin panel) and guests (public
booking). Staff need authenticated, role-aware access. Guests should book online
without registering — registration friction is out of scope for a single-hotel thesis demo.

## Considered Options

1. Session cookies for everyone; mandatory guest accounts
2. JWT for staff (HS256, access + refresh); guests use confirmation code + email
3. JWT access-only (no refresh); single ADMIN role

## Decision Outcome

**Chosen option:** option 2.

- Staff: `POST /api/v1/auth/login` + refresh; **JWT HS256**; access ≈ **60 min**,
  refresh ≈ **24 h**; roles **`ADMIN`** and **`RECEPTIONIST`** only.
- Guests: **no accounts**. Public flow: availability → book → lookup/cancel by
  **confirmation code + email**. Cancellation further requires a refundable
  RatePlan (ADR-0007).
- Public endpoints are unauthenticated; admin API requires Bearer JWT + method security.

### Consequences

- Good: matches real hotel booking UX; clear security boundary for the admin API.
- Good: only two roles — enough for thesis demos without RBAC sprawl.
- Bad / risk: confirmation-code + email is weaker than accounts — acceptable for
  demo; codes use an unambiguous alphabet and are uniqueness-checked.

## More Information

Contract: `docs/api/pms-api.md`. Implemented in Phase 2 (backend) and Phase 3 (UI).
