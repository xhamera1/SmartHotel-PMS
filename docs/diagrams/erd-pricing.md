# ERD — `pricing` schema

Source of truth: `services/pricing-service/migrations/versions/0001_baseline.py`
(Alembic). Update this diagram together with any migration that changes the schema.

Key semantics:

- **No foreign keys into the `pms` schema** — the two services share a PostgreSQL
  instance but never couple at the database level (ADR-0002). `room_type_code` in
  `prediction_log` is a contract-level reference, validated by API, not by FK.
- `event_scores` keeps **history** (an event can be re-scored when its content
  changes); the latest `scored_at` per event is the current score.
- `model_registry` enforces **at most one active model** via a partial unique
  index on `is_active WHERE is_active`.
- `daily_demand` is the aggregation seam: many EventImpactScores → one
  DemandIndicator per HotelNight.
- `prediction_log` is append-only; it feeds monitoring dashboards and the thesis
  evaluation statistics.

```mermaid
erDiagram
    EVENTS ||--o{ EVENT_SCORES : "is scored as"

    EVENTS {
        bigint id PK
        varchar provider "UNIQUE(provider, external_id)"
        varchar external_id
        varchar name
        varchar category
        varchar venue_name
        varchar city
        numeric latitude
        numeric longitude
        numeric distance_km "from the hotel"
        timestamptz starts_at
        timestamptz ends_at
        int expected_attendance
        text url
        jsonb raw_payload "full provider response"
        timestamptz fetched_at
        varchar content_hash "sha256 - change detection"
        varchar status "NEW | SCORED | STALE | IGNORED"
    }

    EVENT_SCORES {
        bigint id PK
        bigint event_id FK "ON DELETE CASCADE"
        smallint impact_score "0..100 (EventImpactScore)"
        numeric confidence "0..1"
        date_array affected_nights
        text rationale "LLM explanation"
        text llm_model
        text prompt_version
        jsonb response_raw "audit trail"
        boolean is_fallback "heuristic scorer used"
        timestamptz scored_at
    }

    DAILY_DEMAND {
        date date PK "HotelNight"
        smallint indicator "0..100 (DemandIndicator)"
        bigint_array top_event_ids
        timestamptz computed_at
    }

    MODEL_REGISTRY {
        bigint id PK
        text version UK
        text algorithm
        text dataset_hash "reproducibility"
        jsonb params
        jsonb metrics "offline evaluation results"
        text feature_schema_hash "serving-time compatibility check"
        text artifact_path
        timestamptz trained_at
        boolean is_active "at most one TRUE (partial unique index)"
    }

    PREDICTION_LOG {
        bigint id PK
        text request_id "correlation id"
        varchar room_type_code "contract-level ref to pms"
        date stay_date "HotelNight"
        jsonb features
        numeric multiplier
        numeric price "recommended BAR"
        text model_version
        timestamptz created_at
    }
```
