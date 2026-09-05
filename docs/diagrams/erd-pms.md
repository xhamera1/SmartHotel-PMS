# ERD — `pms` schema

Source of truth: `services/pms-core/src/main/resources/db/migration/V1__baseline.sql`
(Flyway). Update this diagram together with any migration that changes the schema.

Key semantics not expressible in boxes and lines:

- `reservations.stay` is a **generated half-open daterange** `[check_in, check_out)`;
  the `no_double_booking` GiST exclusion constraint forbids overlapping stays on the
  same room for active statuses (`CONFIRMED`, `CHECKED_IN`) — enforced by the
  database even under concurrent requests.
- `rate_calendar.price` is the **BAR** (Best Available Rate) per (room type, night).
  A rate plan's nightly price is derived as `BAR × rate_plans.price_modifier`
  (ADR-0007); the sellable product is a (RoomType, RatePlan) pair.
- `staff_users` participates in no relationships — staff act on data, they are not
  referenced by it (audit trails come later with structured logging).

```mermaid
erDiagram
    ROOM_TYPES ||--o{ ROOMS : "categorizes"
    ROOM_TYPES ||--o{ RATE_CALENDAR : "has nightly BAR"
    GUESTS ||--o{ RESERVATIONS : "books"
    ROOMS ||--o{ RESERVATIONS : "is assigned to"
    RATE_PLANS ||--o{ RESERVATIONS : "is sold under"

    ROOM_TYPES {
        bigint id PK
        varchar code UK "e.g. STD_DOUBLE"
        varchar name
        text description
        smallint capacity "1..10"
        numeric base_price "min <= base <= max"
        numeric min_price
        numeric max_price
        jsonb amenities
        boolean active
    }

    ROOMS {
        bigint id PK
        varchar room_number UK
        bigint room_type_id FK
        smallint floor
        varchar status "AVAILABLE | OUT_OF_SERVICE"
        text notes
    }

    RATE_PLANS {
        bigint id PK
        varchar code UK "e.g. FLEX, NONREF, BB"
        varchar name
        boolean refundable "drives guest cancellation rights"
        boolean breakfast_included
        numeric price_modifier "applied to BAR, e.g. 0.90"
        boolean active
        smallint sort_order
    }

    GUESTS {
        bigint id PK
        varchar first_name
        varchar last_name
        varchar email UK "unique on lower(email)"
        varchar phone
    }

    RESERVATIONS {
        bigint id PK
        varchar confirmation_code UK "8-char unambiguous alphabet"
        bigint guest_id FK
        bigint room_id FK
        bigint rate_plan_id FK
        date check_in
        date check_out
        daterange stay "GENERATED [check_in, check_out)"
        varchar status "CONFIRMED | CHECKED_IN | CHECKED_OUT | CANCELLED | NO_SHOW"
        smallint adults
        numeric total_price
        char currency "PLN"
        jsonb price_breakdown "per-night price + PriceSource snapshot"
        varchar source "WEB | ADMIN"
        bigint version "optimistic locking"
    }

    RATE_CALENDAR {
        bigint id PK
        bigint room_type_id FK "UNIQUE(room_type_id, date)"
        date date "HotelNight"
        numeric price "BAR"
        varchar source "ML_MODEL | MANUAL | BASE | BASE_FALLBACK"
        smallint demand_indicator "0..100"
        text model_version
        jsonb factors
        timestamptz computed_at
    }
```
