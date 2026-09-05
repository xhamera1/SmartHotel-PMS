# ADR-0007 — Rate plans as static derived rates off the ML-priced BAR

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Patryk Chamera

## Context

In hospitality, the sellable product is not a room type alone but a **room type ×
rate plan** combination: the same Standard Double is sold as a flexible rate, a
cheaper non-refundable rate, or a breakfast-included rate. Modeling this makes the
domain industry-credible and enables realistic cancellation policies.

The risk: the entire dynamic-pricing pipeline (rate calendar, quotes API, ML model,
synthetic data generator) is keyed on (room type, night). Making rate plans a
pricing dimension would multiply that key through every phase of the project.

## Considered options

1. **No rate plans** — room type only. Simplest, but the product model is
   unrealistic and cancellation policy has nothing to hang on.
2. **Rate plans as a full pricing dimension** — the ML model prices every
   (room type, rate plan, night). Realistic but triples the rate calendar,
   changes the quotes contract, complicates the dataset generator and the model,
   and adds no depth to the thesis research questions.
3. **Rate plans with static derived pricing** — the ML pipeline prices only the
   **BAR** (Best Available Rate) per (room type, night), exactly as before; each
   rate plan derives its nightly price as `BAR × price_modifier` (e.g. NONREF =
   BAR × 0.90), rounded to grosz and computed at read/booking time.

## Decision

Option 3. `pms.rate_plans` holds code, name, `refundable`, `breakfast_included`,
`price_modifier`, `active`, `sort_order`. Reservations reference a rate plan and
snapshot the derived per-night prices into `price_breakdown` as always.

- Derived pricing off BAR is standard industry practice, not a shortcut.
- The pricing seam is untouched: `rate_calendar`, the quotes API, the ML model,
  and the data generator all stay keyed on (room type, night).
- Guest self-cancellation additionally requires `refundable = true`; admins can
  always cancel.

## Consequences

- **Positive:** realistic product model at near-zero pricing-pipeline cost;
  availability responses can offer multiple prices per room type; cancellation
  policy becomes a testable business rule.
- **Negative:** rate-plan prices cannot react to demand independently of the BAR;
  per-plan elasticity is out of scope. Cancellation cut-off windows (e.g. "free
  until 3 days before") are deferred — `refundable` is boolean for now.
- If per-plan dynamic pricing is ever needed, it becomes a new ADR superseding
  this one; the schema migration path is additive (a rate_plan dimension on
  `rate_calendar`).
