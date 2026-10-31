# Phase 9 Playwright E2E — Implementation Plan

> **For agentic workers:** execute task-by-task; checkboxes track progress.

**Goal:** Playwright suite E2E-01…11 against dockerized `app+stubs`, thesis docs, CI smoke/full.

**Architecture:** `e2e/` package; API fixtures; admin `storageState`; fault project stops pricing container.

**Tech stack:** Playwright TS, pnpm, Docker Compose, existing `data-testid`s.

## Global Constraints

- Catalog: `docs/qa/e2e-scenario-catalog.md`
- Flake policy: `docs/qa/e2e-flake-policy.md`
- Credentials: `admin@smarthotel.local` / `admin-dev-password`; reception twin
- baseURL: `http://127.0.0.1:8088`; API: `http://127.0.0.1:8080`

---

### Task 1: Thesis docs

- [x] Scenario catalog
- [x] Flake policy
- [x] This plan file

### Task 2: Scaffold `e2e/`

- [x] `package.json`, `tsconfig.json`, `playwright.config.ts`
- [x] `auth.setup.ts` + storage paths
- [x] `helpers/api.ts`, `dates.ts`, `docker.ts`

### Task 3: Fallback banner

- [x] `pricing-fallback-banner` on RateCalendarPage + i18n

### Task 4: Specs

- [x] E2E-01…11 with tags

### Task 5: CI

- [x] main.yml + nightly.yml `app+stubs`, reports

### Task 6: Verify + README / current-status

- [x] Document runbook; mark Phase 9 in progress (🟡 until 3× CI green)
