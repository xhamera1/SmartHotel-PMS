# perf

k6 performance scenarios (smoke / load / stress / spike / soak) with thresholds
encoding the SLOs from Phase 11 of the [implementation plan](../docs/detailed_implementation_plan.md).
`baselines/` holds committed result baselines for nightly regression comparison;
raw run output goes to `results/` (git-ignored).
