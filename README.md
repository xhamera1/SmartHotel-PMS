# SmartHotel-PMS

**Hotel Management System with an Intelligent Dynamic Pricing Engine**
Bachelor's thesis project — Patryk Chamera

A hotel property management system (PMS) with a public booking module, backed by a
machine-learning pricing engine. Prices are recommended by a Random Forest model whose
features include a demand indicator derived from local events, fetched from a public
event API and scored for impact by the Google Gemini LLM.

## Architecture at a glance

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| `services/pms-core` | Java 21 · Spring Boot · Maven | Reservations, rooms, guests, auth, rate calendar |
| `services/pricing-service` | Python 3.12 · FastAPI · scikit-learn · uv | ML price serving, training, event ingestion, Gemini scoring |
| `frontend` | React · TypeScript · Vite | Admin panel + public booking SPA |
| Database | PostgreSQL 17 (schemas `pms` / `pricing`) | Persistence, DB-level booking integrity |
| Delivery & QA | Docker Compose · GitHub Actions · JUnit/pytest/Playwright/k6 | CI/CD with embedded quality gates |
| Observability | Elasticsearch · Kibana · Filebeat | Structured logs, cross-service tracing |

## Documentation

- **[Thesis project description](docs/thesis_project_description.md)** — scope and goals.
- **[Domain glossary](docs/glossary.md)** — the ubiquitous language used in code, schemas, and APIs.
- `docs/adr/` — Architecture Decision Records (design decisions with rationale).

## Repository layout

```text
docs/                 thesis docs, ADRs, API contracts, diagrams, QA docs
services/
  pms-core/           Java Spring Boot backend (PMS core)
  pricing-service/    Python FastAPI pricing microservice (ML, events, datagen)
frontend/             React SPA (admin panel + public booking)
e2e/                  Playwright end-to-end test suite
perf/                 k6 performance scenarios and baselines
infra/                Docker Compose, ELK config, WireMock stubs, seed data
tools/                cross-platform developer scripts
.github/workflows/    CI/CD pipelines (GitHub Actions)
```

## Project status

Foundation complete: repository governance, CI pipeline bootstrap, and containerized
PostgreSQL with isolated per-service schemas. Application services (backend, pricing,
frontend) are under active development.

## Getting started

Prerequisites (pinned toolchain):

| Tool | Pinned | Notes |
|------|--------|-------|
| JDK | 21 LTS (any OpenJDK build; CI uses Temurin 21) | Maven Wrapper `mvnw` ships with the backend scaffold — no global Maven |
| Python | 3.12 (`.python-version`, managed by [uv](https://docs.astral.sh/uv/)) | system Python is not used |
| Node | 24 LTS (`.node-version`) + pnpm | |
| Docker | Docker Desktop with WSL2 backend | |
| [Task](https://taskfile.dev) | 3.x | cross-platform task runner |

```powershell
task            # list all tasks
task up         # start dev infrastructure (PostgreSQL 17, waits until healthy)
task smoke      # up + database smoke checks (schemas, users, btree_gist)
task lint       # all linters (grows with the project)
task test       # all test suites (grows with the project)
task down       # stop infrastructure (data preserved); task db-reset wipes it
```

## License

[MIT](LICENSE) — © 2026 Patryk Chamera.
