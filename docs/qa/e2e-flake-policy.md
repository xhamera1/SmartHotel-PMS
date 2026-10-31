# E2E flake policy (Phase 9)

## Rules

1. **No `waitForTimeout` / fixed sleeps.** Use Playwright web-first assertions
   (`expect(locator).toBeVisible()`, `toHaveURL()`, `toHaveText()`, network
   idle only when unavoidable via `waitForResponse`).
2. **Retries:** `retries: 1` locally and in CI; `trace: 'on-first-retry'`.
3. **Artifacts:** HTML report + JUnit XML + traces/videos on failure uploaded
   from `e2e/playwright-report/` and `e2e/test-results/`.
4. **Quarantine:** If the **same** test fails for a non-product reason on two
   consecutive CI runs (or flakes twice in one day on main):
   - either **fix the root cause** in the same PR, or
   - tag `@quarantine`, exclude from required smoke, and open a **DEF-####**
     entry in `docs/qa/defect-log.md` with reproduction + owner.
5. **Never** `test.skip` / `.only` committed without a DEF reference.
6. **Dates & locale:** always set `locale: 'pl-PL'` and
   `timezoneId: 'Europe/Warsaw'` in Playwright config; seed dates via ISO
   strings into `data-testid` date inputs.
7. **Parallelism:** unique resource names per worker; E2E-10 runs in a serial
   project after the parallel suite (container mutation).

## Stability bar

E2E becomes a **required** GitHub check only after **three consecutive green**
full-suite runs on `main`/`nightly` without new quarantines.
