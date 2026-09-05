# ADR-0004: Monorepo

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Patryk Chamera
- **Plan reference:** D4

## Context and Problem Statement

The project spans two backend services, a frontend, an E2E suite, performance
scripts, and infrastructure code. Should each component live in its own repository
or in a single monorepo?

## Considered Options

1. Monorepo (single repository, path-filtered CI)
2. Polyrepo (one repository per component)

## Decision Outcome

**Chosen option:** monorepo. Cross-service changes (e.g., an API contract change
touching the pricing service, the Java client, and the E2E suite) stay atomic in
one commit/PR; CI is a single pipeline with `paths-filter` scoping jobs to what
changed; thesis reviewers get one artifact to browse. Polyrepo offers no benefit
at this scale and adds versioning/coordination overhead for a solo developer.

### Consequences

- Good: atomic contract changes, one CI, one issue tracker, one clone-to-demo.
- Good: shared governance files (ADRs, QA docs, Taskfile) apply everywhere.
- Bad / risk: CI must be path-filtered to stay fast — implemented from the first
  workflow (`.github/workflows/pr.yml`).

## More Information

Repository layout: plan §4.3.
