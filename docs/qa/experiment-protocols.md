# Experiment protocols (Phase 13 pre-registration)

Committed **before** running thesis experiments so metrics and success thresholds
cannot be cherry-picked after the fact. Execute via `task ml:train`,
`task ml:ablation`, pricing live-smoke, and future `task experiments` once wired.
Outputs land under `artifacts/experiments/` (CSV/JSON/PNG) with a results manifest.

Hotel context: Kraków · PLN · `Europe/Warsaw`. Datagen seed and configs are the
source of synthetic ground truth (see `docs/qa/dataset-spec.md`).

---

## E1 — Model quality vs baselines (RQ1)

| Field | Value |
|-------|--------|
| **Hypothesis** | Random Forest beats B0 (static `m=1`), B1 (rule table), B2 (linear) on the held-out temporal window. |
| **Data** | `datagen/configs/default.yaml`; train ≤ temporal cutoff (~2.5 y), test = last 6 months. |
| **Seeds** | Primary seed from default config; report mean ± std across **5** dataset seeds if time allows (minimum: seed in `default.yaml`). |
| **Metrics** | MAE / RMSE / R² / MAPE on multiplier and on PLN price; segment by room type and event vs non-event nights. |
| **Success** | RF MAE(multiplier) strictly lower than each of B0–B2 on the test window; CI ml-gate must not regress >10% vs `ml/baseline_metrics.json`. |
| **Artifacts** | `artifacts/evaluation/metrics.json`, predicted-vs-actual / residual / importance plots. |

## E2 — Event-feature ablation + revenue simulation (RQ2)

| Field | Value |
|-------|--------|
| **Hypothesis** | Dropping `demand_indicator`, `event_count_active`, `max_event_score` worsens prediction quality and simulated revenue. |
| **Protocol** | Identical pipeline with/without event features (`ml.ablation`). |
| **Metrics** | Same as E1 plus policy simulation: Revenue, RevPAR, ADR, Occupancy vs B0/B1 on held-out period. |
| **Robustness** | Optional ±20% elasticity misspecification. |
| **Success** | With-events RF MAE ≤ without-events MAE; revenue uplift documented even if small (honest null OK). |
| **Artifacts** | `artifacts/experiments/event-ablation/*`. |

## E3 — LLM event scoring (RQ3)

| Field | Value |
|-------|--------|
| **Hypothesis** | Gemini structured scores correlate with synthetic true uplift better than heuristic fallback alone; repeatable at production temperature. |
| **Data** | Synthetic event descriptions from Phase 4 (~60/year × years in tiny/default); known true uplift in datagen. |
| **Model pin** | `GEMINI_MODEL` from `.env` (default `gemini-3.8-flash`); do not mix model strings mid-window. |
| **Metrics** | Spearman ρ vs true uplift; MAE on normalised scale; per-event std over 5 repeats; paraphrase stability; injection canary pass rate; latency p50/p95; fallback rate. |
| **Success** | Injection canaries blocked (schema+clamp); ρ reported honestly; operational stats logged. Live calls only via `live-smoke.yml` / `@pytest.mark.external`. |
| **Artifacts** | Cached `event_scores.response_raw`; analysis CSV under `artifacts/experiments/llm-eval/`. |

## E4 — System quality evidence (RQ4)

| Field | Value |
|-------|--------|
| **Hypothesis** | Layered automated QA (unit → IT → contract → E2E → perf → fault injection) finds defects earlier; pyramid visible in defect journal. |
| **Sources** | CI artifacts, `docs/qa/defect-log.md`, coverage gates, OpenAPI drift, compose kill-pricing, future Playwright/k6. |
| **Metrics** | Defects per taxonomy layer; coverage %; E2E stability; SLO table from Phase 11 when present. |
| **Success** | Journal complete for known defects; at least one cross-service fault-injection path demonstrated (compose integration). |

## E5 (Optional) — Usability

SUS ≥ 5 users on guest booking + receptionist check-in; report score + notes. Not required for MVP defense.

---

## Change control

Any change to hypotheses, metrics, or success thresholds after the first experimental
run requires a new dated section in this file (do not silently edit prior rows).
