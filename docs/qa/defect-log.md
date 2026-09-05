# Defect Journal

Every defect found in the project is logged here — regardless of how it was found
(automated test layer, CI gate, manual verification, demo). This journal feeds the
thesis QA evaluation (plan Phase 13, experiment E4: *defects found per test layer*
as an empirical argument for the test pyramid).

**Rules (plan §5.1):**

1. Log the defect *when it is found*, not retroactively.
2. Fix it test-first where applicable: write the failing regression test, then fix.
3. `Found by` must name the §5.2 taxonomy layer (or `manual`/`CI gate`/`review`).

Severity scale: `Critical` (data loss / security), `High` (feature broken),
`Medium` (degraded/misleading behavior), `Low` (cosmetic).

---

## DEF-0001 — Init script CRLF line endings crash the postgres container

- **Date:** 2026-09-05 · **Phase:** 0 · **Found by:** manual (compose healthcheck / `up --wait` failure)
- **Severity:** High
- **Symptom:** `smarthotel-postgres` crash-looped with exit code 127
  (`Restarting (127)`); `up --wait` reported the container unhealthy.
- **Root cause:** `infra/postgres/init/01-init.sh` was created on Windows with CRLF
  line endings. Inside the Linux container the shebang resolves to `/bin/sh\r` →
  interpreter not found. Files written directly to the working tree bypass
  `.gitattributes` normalization (that applies at checkout/commit).
- **Resolution:** converted the file to LF; all future container-bound files are
  LF-checked. CI enforces "no committed CRLF" via `git ls-files --eol` (pr.yml).
- **Regression guard:** CI hygiene job; `.gitattributes` `* text=auto eol=lf`.

## DEF-0002 — Failed first-run init is silently masked by the restart policy

- **Date:** 2026-09-05 · **Phase:** 0 · **Found by:** manual (verification queries after DEF-0001)
- **Severity:** Medium
- **Symptom:** after the DEF-0001 crash, the container auto-restarted and PostgreSQL
  came up *healthy* — but without the `pms`/`pricing` schemas and users.
- **Root cause:** the postgres image runs `docker-entrypoint-initdb.d` only when
  `PGDATA` is empty. The first (failed) start had already initialized the volume, so
  the restart skipped init entirely; `restart: unless-stopped` turned a one-shot
  init failure into a silently degraded database.
- **Resolution:** documented the remedy (`down --volumes` re-runs init) in
  `infra/compose.yml` header and `infra/README.md`; wiped and re-initialized.
- **Regression guard:** `task smoke` asserts schemas, service users, and
  `btree_gist` exist — a degraded database can no longer pass unnoticed.
