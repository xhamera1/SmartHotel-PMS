# ADR-0014: Access token in memory; refresh in httpOnly cookie

- **Status:** Accepted
- **Date:** 2026-09-16
- **Deciders:** Patryk Chamera
- **Plan reference:** Phase 3 step 2 — Auth session

## Context and Problem Statement

Staff SPA sessions need a short-lived access JWT and a longer-lived refresh
credential. Putting both tokens in `localStorage` (or any JS-readable store)
exposes them to XSS. The SPA must also survive access-token expiry without a
full re-login when a refresh credential is still valid.

## Considered Options

1. **Both tokens in `localStorage` / `sessionStorage`** — simplest SPA pattern;
   refresh sent in JSON body. Easy to debug; fully XSS-exfiltratable.
2. **Access in module memory + refresh in `httpOnly; SameSite=Strict` cookie**
   set by the backend; silent refresh on `401` (and once on app bootstrap).
3. **BFF / confidential session cookie for everything** — strongest browser
   session model; more moving parts than this thesis needs.

## Decision Outcome

**Chosen option:** option 2.

- Login / refresh responses carry **only the access JWT** (+ staff profile) in JSON.
- Refresh JWT is set as cookie `pms_refresh`: `HttpOnly`, `SameSite=Strict`,
  `Path=/api/v1/auth`, `Secure` in prod (`AUTH_COOKIE_SECURE`).
- SPA axios uses `withCredentials`; on `401` it `POST /api/v1/auth/refresh`
  once (deduped), then retries; `POST /api/v1/auth/logout` clears the cookie.
- **Acceptable-simple alternative (option 1):** keep both tokens in memory or
  `sessionStorage` for a pure-demo shortcut — document XSS risk; do not use in
  any deployment facing a real network.

### Consequences

- Good: refresh token is not readable by JavaScript; access token lifetime of XSS
  exposure is limited to the in-memory session.
- Good: `SameSite=Strict` + cookie scoped to `/api/v1/auth` shrinks CSRF surface
  for refresh/logout (CSRF still disabled on the API; defended by SameSite).
- Bad / risk: cross-site SPA hosting needs shared site + CORS credentials;
  `Secure` must be on for HTTPS. Page reload drops access until silent refresh.

## More Information

Related: ADR-0012. Endpoints: `POST /api/v1/auth/login|refresh|logout`.
