# domain

Pricing domain logic, framework-free: price clamping to `[min, max]` guardrails,
half-up rounding to whole PLN, explanation-factor extraction, and column-wise
batch feature-frame construction for serving.

| Module | Role |
|--------|------|
| `pricing.py` | `clamp_and_round` |
| `factors.py` | quote explanation payload |
| `features_batch.py` | vectorized feature frame via `ml.features` |
