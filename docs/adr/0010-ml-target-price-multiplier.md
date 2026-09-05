# ADR-0010: ML target is the revenue-optimal price multiplier

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Patryk Chamera
- **Plan reference:** D7, §3.5

## Context and Problem Statement

The synthetic dataset needs a supervised learning target. Predicting absolute PLN
prices couples the model to each room type’s base band; without a defined
“optimal” price, offline metrics are not honest ground truth.

## Considered Options

1. Predict absolute nightly price (PLN)
2. Predict demand / occupancy only; price elsewhere
3. Predict **multiplier** `optimal_price / base_price`, where `optimal_price` is
   found by grid search on the simulator’s known demand curve (revenue max)

## Decision Outcome

**Chosen option:** option 3. The Random Forest regresses the multiplier; serving
applies `clamp(base_price × multiplier, min_price, max_price)` and rounds to
**grosz** (ADR-0009). The simulator computes the training target by grid search
against the true (hidden) demand function so MAE/metrics are meaningful.

### Consequences

- Good: one model generalises across room types; min/max guardrails stay explicit.
- Good: thesis evaluation has a known optimum to compare against.
- Bad / risk: target quality depends on the simulator — documented in Phase 4/5;
  latent shocks keep the problem non-trivial.

## More Information

Implemented in Phases 4–5 (datagen + training). Related: ADR-0006, ADR-0009.
