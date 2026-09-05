# Contributing & Workflow

Governance for SmartHotel-PMS (Phase 0, step 3 of the
[implementation plan](docs/detailed_implementation_plan.md)). Solo-developer
project, but run with real engineering discipline — the process itself is thesis
material (RQ4).

## Branching — trunk-based development

- `main` is protected: no force pushes, no deletions, required CI check **CI OK**.
  Direct pushes are effectively blocked (a fresh commit cannot have passing checks),
  so all changes land via pull request.
- Branches are **short-lived** (target: merged within 1–2 days) and named
  `feat/…`, `fix/…`, `chore/…`, `docs/…`, `test/…`, `refactor/…`, `ci/…`.
- Merge strategy: **squash-merge** with a Conventional Commit title — keeps `main`
  history clean and changelog-scriptable.

## Commits — Conventional Commits

Format: `type(scope): subject` — imperative, lower-case subject, no trailing period.

- **Types:** `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`, `ci`, `build`
- **Scopes (suggested):** `pms-core`, `pricing`, `frontend`, `e2e`, `perf`, `infra`, `docs`, `qa`
- Breaking change: `!` after the scope + a `BREAKING CHANGE:` footer.

Examples:

```text
feat(pms-core): reservation state machine with night-audit no-show job
fix(pricing): clamp negative multipliers before price rounding
docs(adr): ADR-0007 ML target variable
ci: add schemathesis stage to python job
```

## Pull requests

- Use the PR template (`.github/PULL_REQUEST_TEMPLATE.md`) — the QA checklist is
  mandatory, including for self-review.
- Keep PRs small and single-purpose (guideline: < ~400 changed lines, one concern).
- All CI checks must be green; `task lint` and `task test` must pass locally first.
- Architectural decisions ship together with their ADR (see `docs/adr/README.md`).
- Bugs found during work are logged in `docs/qa/defect-log.md` *when found*, and
  fixed test-first.

## Definition of Done (per change)

1. Code + tests at the appropriate taxonomy layer (`docs/qa/test-strategy.md`).
2. `task lint` and `task test` green locally; CI green.
3. Documentation updated where behavior/decisions changed (plan, ADR, READMEs).
4. No secrets in the diff; `.env` never committed.

## Branch protection (one-time setup)

Requires the [GitHub CLI](https://cli.github.com/) authenticated as the repo owner
(`gh auth login`) and everything pushed:

```powershell
gh api -X PUT repos/xhamera1/SmartHotel-PMS/branches/main/protection --input .github/branch-protection.json
```

The policy lives in [`.github/branch-protection.json`](.github/branch-protection.json)
(required check `CI OK`, no force pushes/deletions, linear history, conversation
resolution; admins included — relax `enforce_admins` only for genuine emergencies).
