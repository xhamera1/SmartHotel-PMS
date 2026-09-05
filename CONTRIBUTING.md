# Contributing & Workflow

Governance for SmartHotel-PMS. Solo-developer project, but run with real
engineering discipline — the process itself is part of the thesis's quality
assurance evaluation.

## Branching — trunk-based development

- Solo project: changes land as **direct commits to `main`** — no PR ceremony.
- `main` is still protected against force pushes and deletions, and history is
  kept linear.
- CI runs on **every push to `main`**; a red run on `main` is fixed forward
  immediately, before starting new work.
- Short-lived branches (`feat/…`, `fix/…`, `docs/…`, …) with a squash-merged PR
  remain an *option* for riskier or larger changes, but are never required.

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

## Self-review before every push

The QA checklist in `.github/PULL_REQUEST_TEMPLATE.md` applies to **every change**,
whether or not a PR is opened:

- Keep commits small and single-purpose (guideline: < ~400 changed lines, one concern).
- `task lint` and `task test` must pass locally before pushing; CI must be green after.
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

The policy lives in [`.github/branch-protection.json`](.github/branch-protection.json):
no force pushes or deletions (admins included), linear history, conversation
resolution on PRs. Direct pushes to `main` are allowed — CI validates every push.
