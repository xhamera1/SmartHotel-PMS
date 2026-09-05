# CI/CD workflows (GitHub Actions)

Planned pipeline (grows incrementally with the project):

| Workflow | Trigger | Contents |
|----------|---------|----------|
| `pr.yml` **(active)** | pull_request, push to main, manual | paths-filter + repo hygiene + compose lint + Java job (Maven verify: Flyway migrations + reservation constraints in PostgreSQL 17 Testcontainers, reports uploaded) + Python job (ruff + Alembic migration cycle against PostgreSQL 17) + frontend placeholder + aggregate `CI OK` status |
| `main.yml` | push to main | full build, image push (GHCR), compose integration suite, Playwright E2E, k6 smoke |
| `nightly.yml` | schedule | full E2E matrix, k6 load/soak, ELK smoke, mutation testing, dependency audit |
| `live-smoke.yml` | manual | real Ticketmaster + Gemini smoke tests (secrets-gated) |

This README is ignored by the Actions runner (only `*.yml`/`*.yaml` files are parsed).
