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

## DEF-0003 — Alembic migration silently rolled back when the schema pre-exists

- **Date:** 2026-09-05 · **Phase:** 1 · **Found by:** manual (post-migration verification query)
- **Severity:** High
- **Symptom:** `task db-migrate:pricing` (dev database) logged
  `Running upgrade -> 0001` and exited 0, but the `pricing` schema contained no
  tables afterwards; every re-run "applied" the same migration again.
- **Root cause:** `migrations/env.py` runs a pre-flight schema-existence check.
  That `SELECT` opens SQLAlchemy's implicit (autobegin) transaction. On the
  pristine-database path (CI, scratch) the code called `commit()` after creating
  the schema — transaction closed, Alembic then began and committed its own. On
  the schema-already-exists path (dev, where infra init pre-creates `pricing`)
  nothing was committed, so Alembic treated the open transaction as
  caller-managed, skipped its own `COMMIT`, and the entire migration rolled back
  on connection close — with zero errors logged. Classic
  works-in-CI-fails-in-dev asymmetry.
- **Resolution:** `_ensure_schema()` now always commits the pre-flight
  transaction, whether or not it created the schema.
- **Regression guard:** the CI python job's migration cycle
  (`upgrade → upgrade → downgrade base → upgrade` + table assertion) exercises
  the pre-existing-schema path, because `downgrade base` drops tables but keeps
  the schema — a regression makes the final assertion fail.
