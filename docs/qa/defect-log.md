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

## DEF-0004 — CI hygiene rejects explicitly required Windows line endings

- **Date:** 2026-09-05 · **Phase:** 1 · **Found by:** review (Maven Wrapper integration)
- **Severity:** Medium
- **Symptom:** adding the official `mvnw.cmd` makes the old hygiene predicate reject
  `i/crlf`, even though `.gitattributes` explicitly requires `eol=crlf` for `.cmd`.
- **Root cause:** the check inspected the index line ending but ignored the
  declared attributes. Reproduced against the wrapper's expected `git ls-files
  --eol` record before changing the predicate.
- **Resolution:** hygiene now allows CRLF only when the record explicitly declares
  `attr/text eol=crlf`; mixed endings and unexpected CRLF still fail.
- **Regression guard:** the tracked wrapper exercises the allowed CRLF path in
  every CI hygiene run; synthetic records verify rejected unexpected CRLF and
  mixed endings, including mixed content in a CRLF-declared file.

## DEF-0005 — Flyway V1 CREATE SCHEMA fails under least-privilege pms_user

- **Date:** 2026-09-16 · **Phase:** 2 · **Found by:** manual (`spring-boot:run` / dev)
- **Severity:** High
- **Symptom:** app connected to Compose Postgres as `pms_user`, Flyway started
  `V1__baseline`, then failed with `ERROR: permission denied for database
  smarthotel` at the `CREATE SCHEMA IF NOT EXISTS pms` line.
- **Root cause:** Compose init already creates schema `pms` and grants `pms_user`
  CONNECT only (no CREATE on the database). PostgreSQL still requires CREATE
  privilege for `CREATE SCHEMA IF NOT EXISTS`, even when the schema already
  exists. Testcontainers used a DB-owner user, so the same script passed in CI.
- **Resolution:** removed `CREATE SCHEMA` from `V1__baseline.sql`. Schema is
  provided by infra init (dev) or Flyway `schemas=pms` as DB owner (tests).
- **Regression guard:** `PmsCoreApplicationIT` + migration ITs; local
  `spring-boot:run` with Compose after a clean volume.

## DEF-0006 — Property test rejected valid winter season_factor near floor

- **Date:** 2026-10-30 · **Phase:** 4 · **Found by:** unit (pytest / Hypothesis)
- **Severity:** Medium
- **Symptom:** `test_season_factor_bounded` failed for
  `season_factor(2020-01-07, amplitude=1.0) ≈ 0.0066` (assertion required `> 0.1`).
- **Root cause:** With amplitude 1.0 the sinusoid can approach 0; production code
  deliberately clamps with `max(..., 1e-3)`. The property test used a tighter
  lower bound than the implemented contract, while configs only use amplitude ≤ 0.35.
- **Resolution:** Assert `1e-3 <= result < 5.0` for the full amplitude domain;
  added `test_season_factor_business_amplitude_range` for amplitude ≤ 0.5 expecting
  `[0.2, 3.0]`. Season formula unchanged (avoids datagen golden drift).
- **Regression guard:** both Hypothesis tests in `tests/datagen/test_properties.py`.

## DEF-0007 — Sync pipeline skipped scoring new/changed events on empty cache query

- **Date:** 2026-10-30 · **Phase:** 7 · **Found by:** unit
  (`tests/events/test_sync.py::test_sync_pipeline_with_mocked_deps`)
- **Severity:** High
- **Symptom:** `events_to_score == 0` despite upsert returning
  `is_new_or_changed=True`.
- **Root cause:** After upsert, sync filtered candidates with
  `events_needing_scoring`. When that query returned an empty set (or a mock
  engine yielded no rows), new/changed events were treated as cache hits and
  skipped — content changes never forced a rescore.
- **Resolution:** Always score `is_new_or_changed` events; use the cache query
  only to pick up unchanged events that lack a score for the current
  prompt/model. Summary still reports cache hits for unchanged+scored rows.
- **Regression guard:** `test_sync_pipeline_with_mocked_deps`.

## DEF-0008 — README project status lagged behind Phase 8 delivery

- **Date:** 2026-10-30 · **Phase:** docs · **Found by:** review / status audit
- **Severity:** Low
- **Symptom:** Root README still described “foundation / Phase 1–2” while the
  codebase had completed Track A+B and Phase 8 integration.
- **Root cause:** Status prose was not updated after pricing, frontend, and
  integration landed.
- **Resolution:** README “Project status” now states Phases 0–8 complete and
  links `docs/current-status-30-october.md`.
- **Regression guard:** status doc + README cross-check on future phase exits.

## DEF-0009 — Admin events proxy dropped LLM confidence and rationale

- **Date:** 2026-10-30 · **Phase:** 8 · **Found by:** review / status audit
- **Severity:** Medium
- **Symptom:** Admin Events UI always showed empty confidence/rationale; PMS mapped
  `null, null` in `PricingProxyController.toEventResponse`.
- **Root cause:** Pricing `GET /events` did not expose score metadata; PMS DTO
  lacked fields and hard-coded nulls.
- **Resolution:** Pricing returns `confidence` + `rationale` from latest
  `event_scores`; `PricingEventItem` + proxy map them through; OpenAPI regenerated.
- **Regression guard:** `test_events_returns_items` asserts both fields.

## DEF-0010 — Quote serving approximated event features from demand indicator

- **Date:** 2026-10-30 · **Phase:** 6 · **Found by:** review / status audit
- **Severity:** Medium
- **Symptom:** `event_count_active` / `max_event_score` in quotes were derived as
  `1 if indicator>0` / `indicator`, diverging from training features.
- **Root cause:** `fetch_demand_by_dates` only selected `indicator`.
- **Resolution:** Join `top_event_ids` with latest event scores; count and max
  impact drive the snapshot.
- **Regression guard:** `tests/domain/test_demand_snapshots.py`.

## DEF-0011 — Datagen golden hashes were never committed

- **Date:** 2026-10-30 · **Phase:** 4 · **Found by:** review / status audit
- **Severity:** Medium
- **Symptom:** `golden_hashes.json` missing; reproducibility gate could not fail CI
  on generator drift until first local create-and-skip run.
- **Root cause:** Initial golden file never committed after Phase 4.
- **Resolution:** Committed `tests/datagen/golden_hashes.json` from tiny config.
- **Regression guard:** `test_golden_datagen_snapshot` compares committed hashes.

## DEF-0012 — Pricing startup soft-failed on model schema mismatch

- **Date:** 2026-10-30 · **Phase:** 6 · **Found by:** review (plan Phase 6 exit)
- **Severity:** High
- **Symptom:** Schema hash mismatch logged and left `ready=false` instead of
  failing the process; easy to miss in ops.
- **Root cause:** `load_active_model` returned `None` on mismatch; lifespan
  swallowed load errors.
- **Resolution:** Raise `ModelSchemaMismatchError` on hash mismatch; lifespan
  fail-fast if no model can be loaded (fixture still allowed for local/demo).
- **Regression guard:** `tests/api/test_model_loader_fail_fast.py`.

## DEF-0013 — Manual `task seed` bypassed Flyway history

- **Date:** 2026-10-30 · **Phase:** 2 · **Found by:** review / status audit
- **Severity:** Medium
- **Symptom:** Taskfile `seed` piped V1/V2 SQL via `psql`, creating schema/seed
  without `flyway_schema_history` — risk of duplicate objects or Flyway checksum
  fights on next app start.
- **Root cause:** Interim Phase-0 seed task never retired after Flyway ownership.
- **Resolution:** `task seed` is now a reminder; docs in `infra/README` and
  `pms-core/README` state Flyway owns migrations+seeds.
- **Regression guard:** documented workflow (`db-reset` → `run:pms`).

## DEF-0014 — Compose `app` profile had no frontend; stubs/ELK were README-only

- **Date:** 2026-10-30 · **Phase:** 3/9/10 · **Found by:** status audit
- **Severity:** Medium
- **Symptom:** Full-stack demo required separate `pnpm dev`; WireMock/ELK profiles
  documented but absent from `compose.yml`.
- **Root cause:** Services deferred after Phase 8 integration focused on APIs.
- **Resolution:** `frontend` nginx multi-stage image on profile `app`; WireMock
  mappings + `stubs` service; ES/Kibana/Filebeat on `observability`; `task up:app`.
- **Regression guard:** `docker compose … config --quiet`; CI compose `app` build.

## DEF-0015 — Default Gemini model string was not a current Flash pin

- **Date:** 2026-10-30 · **Phase:** 7 · **Found by:** review (R1 / status audit)
- **Severity:** Medium
- **Symptom:** Defaults used `gemini-3.8-flash`, which does not match the plan’s
  Flash-class pin and risks live-smoke failures.
- **Root cause:** Placeholder string never updated after Phase 7.
- **Resolution:** Default `GEMINI_MODEL=gemini-2.5-flash` across settings, compose,
  `.env.example`, live-smoke, ADR-0011.
- **Regression guard:** ADR-0011 pin note; live-smoke uses env default.

## DEF-0016 — Rate-calendar refresh horizon defaulted to 365 vs plan 180

- **Date:** 2026-10-30 · **Phase:** 8 · **Found by:** status audit
- **Severity:** Low
- **Symptom:** Default `PRICING_REFRESH_HORIZON_DAYS` was 365 (plan §3.4 / Phase 8: 180).
- **Resolution:** Defaults in `application.yml` / `application-dev.yml` set to 180;
  env override still supported. Admin URL layout under `/admin/pricing/*` kept
  (FE already wired); OpenAPI tag description updated.
- **Regression guard:** config defaults + OpenApiConfig tag text.

## DEF-0017 — Same-day guest booking could never self-cancel

- **Date:** 2026-10-30 · **Phase:** 2/3 · **Found by:** manual (guest cancel 409)
- **Severity:** High
- **Symptom:** `POST …/reservations/{code}/cancel` returned 409
  `illegal-state-transition` (“only allowed before the check-in date”) for
  confirmation `3KBDTVD3` with `check_in = today` (Europe/Warsaw). UI still showed
  Cancel for any CONFIRMED refundable stay.
- **Root cause:** Guard used `today < check_in` (state-machine table T3). Public
  search allows check-in = today, so a same-day booking was immediately past the
  cancel window. FE did not mirror the date cut-off.
- **Resolution:** Guest cancel allowed while `today ≤ check_in` and status still
  `CONFIRMED`; reject only after the check-in calendar day. FE hides Cancel and
  shows `cancelWindowClosed` when hotel today > check-in. Diagram T3 updated.
- **Regression guard:** `shouldAllowGuestCancelOnCheckInDateWhenStillConfirmed`,
  `shouldRejectGuestCancelAfterCheckInDate`.

## DEF-0018 — Guest cancel showed both success and “already cancelled”

- **Date:** 2026-10-30 · **Phase:** 3 · **Found by:** manual (manage booking UX)
- **Severity:** Low
- **Symptom:** After a successful cancel, Manage Booking showed both
  “Rezerwacja została anulowana.” and “Ta rezerwacja jest już anulowana.”
  Cancel ran immediately on button click (no confirmation).
- **Root cause:** `onSuccess` wrote `CANCELLED` into the lookup cache, so the
  static `status === 'CANCELLED'` info alert rendered alongside
  `cancelMutation.isSuccess`.
- **Resolution:** Show `alreadyCancelled` only when cancelled and not just
  cancelled in this session; open a confirm dialog before calling cancel.
- **Regression guard:** `already-cancelled` vs `cancel-success` mutual exclusion
  on ManageBookingPage; `cancel-confirm-dialog` before mutate.

## DEF-0019 — Ticketmaster heuristic impact stuck at 0

- **Date:** 2026-10-30 · **Phase:** 7 · **Found by:** manual (admin Events UI)
- **Severity:** High
- **Symptom:** All live Ticketmaster events showed wpływ=0, confidence 0.6,
  identical rationales `~0 attendance`.
- **Root cause:** Discovery API has no capacity; mapper wrongly treated
  `priceRanges.max` as seats (ticket price). Heuristic used
  `max(1, attendance)` → factor `1/5000` → rounded score 0. Gemini was
  unavailable so every row was heuristic fallback.
- **Resolution:** Category attendance priors when capacity unknown; stop using
  price ranges as attendance; rationale marks `(assumed)`.
- **Regression guard:** `test_heuristic_score_missing_attendance_uses_category_prior`,
  `test_ticketmaster_ignores_price_range_as_attendance`.
