# CI/CD workflows (GitHub Actions)

Planned pipeline (grows incrementally with the project):

| Workflow | Trigger | Contents |
|----------|---------|----------|
| `pr.yml` **(active)** | pull_request, push to main, manual | paths-filter + repo hygiene + compose lint + Java job (Maven verify: Flyway migrations + reservation constraints in PostgreSQL 17 Testcontainers, reports uploaded) + Python job (ruff, pytest, deterministic ML metric gate, Alembic migration cycle) + frontend checks + aggregate `CI OK` status |
| `main.yml` **(active)** | push to main | image build & push (GHCR), full test suite (unconditional), compose integration + fallback, Playwright E2E smoke (when configured), k6 smoke (when configured) |
| `nightly.yml` **(active)** | schedule (02:30 UTC) | full E2E matrix (chromium + firefox), k6 load/soak + baseline compare, ELK observability smoke, PIT/mutmut mutation testing (report-only), dependency audit (Trivy + gitleaks + npm audit) |
| `live-smoke.yml` | manual | real Ticketmaster + Gemini smoke tests (secrets-gated) |

This README is ignored by the Actions runner (only `*.yml`/`*.yaml` files are parsed).
