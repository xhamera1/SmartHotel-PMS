# frontend

React SPA — Vite · TypeScript (`strict`) · MUI · TanStack Query · React Router.

Public booking + role-guarded admin panel. API types generated from
`docs/api/pms-openapi.json` via `openapi-typescript`.

## Prerequisites

- Node 24+ (see repo `.node-version`)
- pnpm 11+

## Scripts

```text
pnpm install
pnpm dev              # http://localhost:5173 (proxies /api → VITE_API_BASE_URL)
pnpm lint
pnpm typecheck
pnpm build
pnpm test             # vitest (booking zod schemas, …)
pnpm generate:api     # regenerate src/shared/api/schema.d.ts
pnpm check:api        # fail if schema.d.ts drifts from committed OpenAPI
```

## Layout

```text
src/
  app/                 App shell, router
  features/
    booking/           public search → checkout → confirmation → manage
    admin/             dashboard, reservations, guests, rates, events; ADMIN CRUD rooms
  shared/
    api/               axios client, TanStack Query, OpenAPI schema
    auth/              in-memory session, RequireAuth / RequireRole
    theme/             MUI theme
    lib/               request-id, hotel dates, PLN formatting
```

## Public booking

- Search (date range + guests) → availability cards (nightly BAR + rate-plan totals from API)
- Checkout: React Hook Form + zod guest schema + mock payment → `POST /reservations`
- Confirmation code page; manage lookup/cancel by code + email
- Prices via `Intl.NumberFormat('pl-PL', { currency: 'PLN' })` only from API numbers

## UX / E2E hooks

- Loading: `PageSkeleton`; empty: `EmptyState`; HTTP errors: `ProblemAlert` (RFC 7807 fields)
- Render crashes: `AppErrorBoundary` at the app root
- Keyboard: skip-to-content, `:focus-visible` outlines, reservation rows open on Enter/Space
- `data-testid` convention: kebab-case, feature-prefixed — see `src/shared/ui/testids.ts`

## Auth (ADR-0014)

- Access JWT + staff profile in module memory only (never `localStorage`).
- Refresh JWT in backend-set `httpOnly; SameSite=Strict` cookie (`pms_refresh`).
- Axios uses `withCredentials`; attaches `Authorization: Bearer …` and a fresh `X-Request-ID`.
- On `401`, tries `POST /api/v1/auth/refresh` once (cookie, no body), then clears the session.
- Admin route guard runs one silent refresh before redirecting to login (page reload restore).
- Logout calls `POST /api/v1/auth/logout` to clear the cookie.

## OpenAPI contract

1. Export from pms-core (Testcontainers):

```text
cd services/pms-core
.\mvnw.cmd -B -ntp "-Dit.test=OpenApiExportIT" "-Dopenapi.export=true" verify
```

2. Regenerate frontend types: `pnpm generate:api`

CI runs `pnpm check:api` so uncommitted type drift fails the build.
