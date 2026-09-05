# ADR-0011: Gemini structured event scores with heuristic fallback

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Patryk Chamera
- **Plan reference:** D9, §3.6

## Context and Problem Statement

Local events must become a numeric feature for pricing. Free-form LLM prose is
unstable; a hard dependency on Gemini would break the pipeline on quota/outage;
the exact free-tier model string may change under a student licence.

## Considered Options

1. Hand-tuned rules only (no LLM)
2. Unstructured Gemini text parsed ad hoc
3. Structured Gemini JSON scores (0–100) → nightly demand indicator, plus a
   heuristic fallback when the LLM is unavailable

## Decision Outcome

**Chosen option:** option 3.

- Gemini returns **structured JSON** per event: `impact_score` 0–100, confidence,
  `affected_nights`, short rationale (schema-enforced; low temperature).
- Scores aggregate into a **DemandIndicator** 0–100 per HotelNight.
- On error/quota: **heuristic fallback** scorer; rows flagged `is_fallback=true`.
- Prompt text and model id are **versioned and stored** with every score.
- **Exact model string is deferred** until Phase 7 — chosen from whatever Flash-class
  model remains free under Google AI Studio / student access, then pinned in config.
- Live Gemini calls only in manual `live-smoke` / thesis experiments; CI always stubs.

### Consequences

- Good: pipeline never stalls without Gemini; RQ3 evaluation stays possible.
- Good: free-tier constraint is explicit; pin happens when the licence is known.
- Bad / risk: model retirement mid-thesis — re-pin and re-run evaluation (never mix
  versions in one experiment window).

## More Information

Phases 7 and 13 (E3). Related: glossary EventImpactScore / DemandIndicator.
Env: `GEMINI_API_KEY`, `GEMINI_MODEL`, `PROMPT_VERSION`, `GEMINI_DAILY_CALL_BUDGET`.
