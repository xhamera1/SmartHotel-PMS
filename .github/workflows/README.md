# CI/CD workflows (GitHub Actions)

Planned pipeline (grows phase by phase, consolidated in Phase 12 of the
[implementation plan](../../docs/detailed_implementation_plan.md)):

| Workflow | Trigger | Contents |
|----------|---------|----------|
| `pr.yml` | pull_request | paths-filtered lint / type-check / unit + integration tests, coverage gates, contract drift, ML gate |
| `main.yml` | push to main | full build, image push (GHCR), compose integration suite, Playwright E2E, k6 smoke |
| `nightly.yml` | schedule | full E2E matrix, k6 load/soak, ELK smoke, mutation testing, dependency audit |
| `live-smoke.yml` | manual | real Ticketmaster + Gemini smoke tests (secrets-gated) |

This README is ignored by the Actions runner (only `*.yml`/`*.yaml` files are parsed).
