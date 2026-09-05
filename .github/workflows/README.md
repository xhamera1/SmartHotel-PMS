# CI/CD workflows (GitHub Actions)

Planned pipeline (grows incrementally with the project):

| Workflow | Trigger | Contents |
|----------|---------|----------|
| `pr.yml` **(active)** | pull_request, push to main | paths-filter + repo hygiene + compose lint + python job (ruff + Alembic migration cycle against PostgreSQL 17) + self-enforcing placeholders (java/frontend) + aggregate `CI OK` status; placeholders become real steps as components are scaffolded |
| `main.yml` | push to main | full build, image push (GHCR), compose integration suite, Playwright E2E, k6 smoke |
| `nightly.yml` | schedule | full E2E matrix, k6 load/soak, ELK smoke, mutation testing, dependency audit |
| `live-smoke.yml` | manual | real Ticketmaster + Gemini smoke tests (secrets-gated) |

This README is ignored by the Actions runner (only `*.yml`/`*.yaml` files are parsed).
