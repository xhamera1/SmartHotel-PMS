# API Contracts

Committed OpenAPI artifacts — the contract source of truth between services (plan §3.3, D19):

- `pms-api.md` / exported PMS OpenAPI spec — public + admin API (Phase 1 design, Phase 2 export).
- `pricing-openapi.json` — internal pricing API, exported from FastAPI (Phase 6).
  CI fails when the generated spec drifts from the committed copy.
