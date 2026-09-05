# Test Strategy (living document)

Baseline copied from the implementation plan §5 on 2026-09-05. **This copy is the
one that evolves** — when practice diverges from the plan, update this file (and the
plan if the divergence is architectural). The taxonomy layer names below are the
canonical vocabulary used by the defect journal and CI job names.

## Principles

1. **Shift-left:** every phase ships with its tests; no phase exits with untested code.
2. **Test pyramid discipline:** many fast unit tests, a solid layer of integration
   tests against real PostgreSQL (Testcontainers), few but meaningful E2E journeys.
3. **Determinism:** CI never calls real external APIs. Ticketmaster and Gemini are
   always stubbed (WireMock / SDK fakes / static providers). Real-API smoke tests
   live only in the manually triggered `live-smoke.yml` workflow.
4. **Every bug becomes a regression test first** (test-first bug fixing) and an
   entry in [`defect-log.md`](defect-log.md).
5. **Time is injectable everywhere** (`java.time.Clock` bean in Spring; a `now()`
   provider in Python) — no test sleeps or depends on the wall clock.
6. **ML/LLM testing is first-class:** metric regression gates, metamorphic tests,
   golden prompt tests (plan Phases 5, 7, 13).

## Test taxonomy & tooling

| Layer | Scope | Tools | Runs in |
|-------|-------|-------|---------|
| Unit (Java) | Domain rules, services with mocked ports | JUnit 5, Mockito, AssertJ | every PR |
| Persistence slice (Java) | Repositories, constraints, migrations | `@DataJpaTest` + Testcontainers PostgreSQL, Flyway | every PR |
| Web slice (Java) | Serialization, validation, security rules | `@WebMvcTest`, spring-security-test | every PR |
| API integration (Java) | Full Spring context, black-box HTTP | `@SpringBootTest(RANDOM_PORT)` + RestAssured + Testcontainers | every PR |
| Architecture (Java) | Layering rules | ArchUnit | every PR |
| Unit (Python) | Features, datagen math, scoring, clamping | pytest, hypothesis | every PR |
| API + DB integration (Python) | FastAPI endpoints, registry, prediction log | httpx TestClient, testcontainers-python, respx | every PR |
| Contract | OpenAPI drift, provider fuzzing, consumer stubs | committed `openapi.json` + schemathesis + WireMock | every PR |
| Data contracts | Dataset schema validation | pandera | PR (datagen paths) |
| ML behavioral | Metamorphic relations, metric regression gate | pytest + `baseline_metrics.json` | PR (ml paths) + nightly |
| Frontend unit/component | Components, hooks, forms, guards | Vitest, React Testing Library, MSW | every PR |
| E2E | User journeys incl. fault injection | Playwright vs. `app+stubs` compose stack | main + nightly |
| Performance | SLO thresholds, regression vs. baseline | k6 (`constant-arrival-rate`) | smoke on main, full nightly |
| Security | Dependency/image/secret scanning | Dependabot, Trivy, gitleaks | every PR + nightly |
| Mutation (optional) | Test-suite strength | PIT (Java), mutmut (Python) | nightly, report-only |

## Coverage targets & quality gates

| Gate | Threshold |
|------|-----------|
| JaCoCo line coverage — `pms-core` domain + service packages | ≥ 80 % (branch ≥ 70 %) |
| pytest-cov — `pricing-service` `ml/`, `domain/`, `events/` | ≥ 85 % |
| Frontend coverage on logic-bearing components/hooks | ≥ 70 % |
| Lint/format/type-check (all languages) | zero errors |
| OpenAPI drift | zero uncommitted diff |
| ML metric gate | MAE(multiplier) regression ≤ 10 % vs. baseline |
| E2E on main | 100 % pass, retries ≤ 1 |
| k6 thresholds | all SLOs green (plan Phase 11) |
| Repo hygiene | no committed CRLF (`git ls-files --eol`) |

## Where strict TDD applies

Red-green-refactor is mandatory for: availability computation, the reservation
state machine, price clamping and override precedence, demand-indicator
aggregation, feature engineering, datagen math — and for **every bug fix**
(regression test first). Test-after is acceptable for controllers, DTO mapping,
configuration, and UI layout.

## Test data management

- Builders/Object-Mother in Java, factory fixtures in pytest, API-seeding helpers
  for Playwright.
- E2E tests create uniquely-named data per test (UUID-suffixed) for parallel safety;
  CI stacks start from a fresh database.
- A committed golden fixture set (tiny dataset + tiny trained model) serves API
  tests — tests never retrain models.

## Status log

| Date | Change |
|------|--------|
| 2026-09-05 | Baseline adopted (Phase 0). Active gates so far: compose config lint, DB smoke checks, CRLF hygiene. |
