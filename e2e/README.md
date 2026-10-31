# e2e — Playwright (Phase 9)

End-to-end suite against the dockerized stack (`compose` profiles **`app` + `stubs`**).
Scenario catalog (thesis): [`docs/qa/e2e-scenario-catalog.md`](../docs/qa/e2e-scenario-catalog.md).
Flake policy: [`docs/qa/e2e-flake-policy.md`](../docs/qa/e2e-flake-policy.md).
Local run pitfalls (thesis notes): [`docs/qa/e2e-local-run-notes.md`](../docs/qa/e2e-local-run-notes.md).

## Prerequisites

```bash
# ALWAYS from repo root (not from e2e/) — .env lives here
cp -n .env.example .env   # if needed
# EVENT_PROVIDER=static recommended for deterministic E2E-11
docker compose --env-file .env -f infra/compose.yml --profile app --profile stubs up -d --build --wait
```

Frontend: `http://localhost:8088` · API: `http://localhost:8080` (prefer `localhost` over `127.0.0.1` for CORS)

## Install & run

```bash
cd e2e
pnpm install
pnpm exec playwright install chromium   # enough for default suite
pnpm test                               # chromium + fault (E2E-10)
pnpm test:smoke                         # @smoke only
```

Optional Firefox (nightly parity):

```bash
pnpm exec playwright install firefox
pnpm test:firefox
```

On Git Bash / Windows avoid `pnpm test -- --project=…` — the bare `--` can be passed through literally and ignore project filters. Prefer the scripts above.

Env overrides: `E2E_BASE_URL`, `E2E_API_URL`, `E2E_ADMIN_EMAIL`, `E2E_ADMIN_PASSWORD`.

## Projects

| Project | Scope |
|---------|--------|
| `setup` | Admin + receptionist `storageState` |
| `chromium` / `firefox` | E2E-01…09, 11 |
| `fault` | E2E-10 only (`docker stop smarthotel-pricing`); runs **after** `chromium` so refresh specs are not starved |

## Tags

- `@smoke` — E2E-01, 07, 10 (CI PR/main smoke)
- `@fault` — E2E-10
- `@quarantine` — see flake policy + DEF entry

## CI

`main.yml` → smoke; `nightly.yml` → full chromium(+fault) and firefox.
Stability bar: **3 consecutive green** runs before required check on `main`.
