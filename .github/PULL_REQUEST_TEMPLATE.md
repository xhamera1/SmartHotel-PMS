# Summary

<!-- What does this PR do and why? Link the plan phase/step it implements, e.g. "Phase 2, step 5 (availability engine)". -->

**Plan reference:**
**Type:** feat / fix / chore / docs / test / refactor / perf / ci

## QA checklist (mandatory, including self-review)

- [ ] `task lint` green locally
- [ ] `task test` green locally
- [ ] New/changed logic is covered by tests at the right taxonomy layer (`docs/qa/test-strategy.md`)
- [ ] Bug fix? The regression test was written first and fails without the fix
- [ ] Defect journal (`docs/qa/defect-log.md`) updated if a defect was found
- [ ] No secrets/credentials/PII in the diff (`.env` untouched)
- [ ] Docs updated where behavior or decisions changed (plan / ADR / READMEs)
- [ ] Architectural decision? ADR added and indexed (`docs/adr/`)
- [ ] DB migration? Idempotent, tested against a clean database — or n/a
- [ ] UI change? Screenshot/GIF attached — or n/a

## Self-review notes

<!-- Anything a reviewer (or future you) should look at twice: trade-offs, known limitations, follow-ups. -->
