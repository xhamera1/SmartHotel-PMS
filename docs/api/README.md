# API Contracts

The contract source of truth between services (D19).

Current (design-time contracts — endpoint inventories, conventions, canonical payloads):

- [`pms-api.md`](pms-api.md) — public booking + admin API of pms-core.
- [`pricing-api.md`](pricing-api.md) — internal pricing API (quotes, demand, model).

Once the services are scaffolded, CI exports the generated OpenAPI specs
(`pms-openapi.json`, `pricing-openapi.json`) into this directory and fails when a
generated spec drifts from the committed copy; the design docs then shrink to
conventions + rationale.
