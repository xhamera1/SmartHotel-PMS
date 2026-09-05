# e2e

Playwright end-to-end suite (TypeScript) running against the dockerized stack
(`app + stubs` compose profiles — external APIs always stubbed). Scenario catalog
E2E-01…E2E-11 including fault injection (pricing service killed mid-flow) is defined
in Phase 9 of the [implementation plan](../docs/detailed_implementation_plan.md).
