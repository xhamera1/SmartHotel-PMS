-- =============================================================================
-- V1__baseline.sql — pms schema baseline
--
-- Owned by Flyway (pms-core service). Design notes:
--   * Enum-like columns are VARCHAR + CHECK (not native PG enums) to keep
--     future migrations painless.
--   * Business dates (check_in/check_out, calendar dates) are DATE — hotel-local
--     calendar, no timezone. Audit timestamps are TIMESTAMPTZ (UTC).
--   * Money is NUMERIC(10,2), PLN only.
--   * updated_at is maintained by JPA auditing, not DB triggers.
-- =============================================================================

-- btree_gist enables the equality operator on room_id inside the GiST exclusion
-- constraint below. Trusted extension; pre-created by infra/postgres/init in dev,
-- created here for pristine databases (Testcontainers).
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE SCHEMA IF NOT EXISTS pms;

-- ---------------------------------------------------------------------------
-- Staff (the only authenticated actors; guests use guest checkout)
-- ---------------------------------------------------------------------------
CREATE TABLE pms.staff_users (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(72)  NOT NULL,          -- BCrypt
    full_name     VARCHAR(120) NOT NULL,
    role          VARCHAR(20)  NOT NULL CHECK (role IN ('ADMIN', 'RECEPTIONIST')),
    active        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Room types — the priced dimension (all pricing is per RoomType, never per Room)
-- ---------------------------------------------------------------------------
CREATE TABLE pms.room_types (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code        VARCHAR(30)   NOT NULL UNIQUE,
    name        VARCHAR(100)  NOT NULL,
    description TEXT,
    capacity    SMALLINT      NOT NULL CHECK (capacity BETWEEN 1 AND 10),
    base_price  NUMERIC(10,2) NOT NULL CHECK (base_price > 0),
    min_price   NUMERIC(10,2) NOT NULL CHECK (min_price > 0),
    max_price   NUMERIC(10,2) NOT NULL,
    amenities   JSONB         NOT NULL DEFAULT '[]'::jsonb,
    active      BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT room_types_price_band CHECK (min_price <= base_price AND base_price <= max_price)
);

-- ---------------------------------------------------------------------------
-- Rooms — physical units; guests book a RoomType, the system assigns a Room
-- ---------------------------------------------------------------------------
CREATE TABLE pms.rooms (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    room_number  VARCHAR(10) NOT NULL UNIQUE,
    room_type_id BIGINT      NOT NULL REFERENCES pms.room_types (id),
    floor        SMALLINT,
    status       VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE'
                 CHECK (status IN ('AVAILABLE', 'OUT_OF_SERVICE')),
    notes        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_rooms_room_type ON pms.rooms (room_type_id);

-- ---------------------------------------------------------------------------
-- Rate plans — the commercial terms a room type is sold under.
-- The guest-facing product is a (RoomType, RatePlan) pair. Each plan's nightly
-- price is DERIVED from the room type's BAR (rate_calendar) via price_modifier;
-- dynamic (ML) pricing operates only on the BAR. See ADR-0007.
-- ---------------------------------------------------------------------------
CREATE TABLE pms.rate_plans (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code               VARCHAR(30)   NOT NULL UNIQUE,
    name               VARCHAR(100)  NOT NULL,
    description        TEXT,
    refundable         BOOLEAN       NOT NULL,
    breakfast_included BOOLEAN       NOT NULL DEFAULT FALSE,
    price_modifier     NUMERIC(5,4)  NOT NULL
                       CHECK (price_modifier > 0 AND price_modifier <= 2),
    active             BOOLEAN       NOT NULL DEFAULT TRUE,
    sort_order         SMALLINT      NOT NULL DEFAULT 0,
    created_at         TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ   NOT NULL DEFAULT now()
);

COMMENT ON COLUMN pms.rate_plans.price_modifier IS
    'Multiplier applied to the room type''s BAR from rate_calendar, e.g. 0.90 for a non-refundable plan. Result rounded to grosz.';

-- ---------------------------------------------------------------------------
-- Guests — minimal PII, deduplicated by email (case-insensitive)
-- ---------------------------------------------------------------------------
CREATE TABLE pms.guests (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name VARCHAR(80)  NOT NULL,
    last_name  VARCHAR(80)  NOT NULL,
    email      VARCHAR(255) NOT NULL,
    phone      VARCHAR(30),
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX uq_guests_email ON pms.guests (lower(email));

-- ---------------------------------------------------------------------------
-- Reservations — the domain centerpiece
-- ---------------------------------------------------------------------------
CREATE TABLE pms.reservations (
    id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    confirmation_code VARCHAR(12) NOT NULL UNIQUE,
    guest_id          BIGINT      NOT NULL REFERENCES pms.guests (id),
    room_id           BIGINT      NOT NULL REFERENCES pms.rooms (id),
    rate_plan_id      BIGINT      NOT NULL REFERENCES pms.rate_plans (id),
    check_in          DATE        NOT NULL,
    check_out         DATE        NOT NULL,
    -- Half-open Stay [check_in, check_out): same-day turnover is conflict-free
    -- by construction. DB-managed; never mapped as writable in JPA.
    stay              daterange   GENERATED ALWAYS AS (daterange(check_in, check_out, '[)')) STORED,
    status            VARCHAR(20) NOT NULL DEFAULT 'CONFIRMED'
                      CHECK (status IN ('CONFIRMED', 'CHECKED_IN', 'CHECKED_OUT', 'CANCELLED', 'NO_SHOW')),
    adults            SMALLINT    NOT NULL CHECK (adults >= 1),
    total_price       NUMERIC(10,2) NOT NULL CHECK (total_price >= 0),
    currency          CHAR(3)     NOT NULL DEFAULT 'PLN',
    price_breakdown   JSONB       NOT NULL,   -- per-night price + PriceSource snapshot (auditability)
    source            VARCHAR(10) NOT NULL CHECK (source IN ('WEB', 'ADMIN')),
    version           BIGINT      NOT NULL DEFAULT 0,   -- optimistic locking (@Version)
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT reservations_dates_valid CHECK (check_out > check_in),
    -- The database-level guarantee against double bookings: no two reservations
    -- in an active status may overlap on the same room, even under concurrency.
    CONSTRAINT no_double_booking EXCLUDE USING gist (room_id WITH =, stay WITH &&)
        WHERE (status IN ('CONFIRMED', 'CHECKED_IN'))
);

CREATE INDEX idx_reservations_guest ON pms.reservations (guest_id);
CREATE INDEX idx_reservations_status_check_in ON pms.reservations (status, check_in);

COMMENT ON COLUMN pms.reservations.stay IS
    'Half-open [check_in, check_out): the check-out date is not a HotelNight of this stay.';

-- ---------------------------------------------------------------------------
-- Rate calendar — precomputed BAR per (RoomType, HotelNight); the only place
-- the booking path reads prices from (never a synchronous ML call). See ADR-0006.
-- ---------------------------------------------------------------------------
CREATE TABLE pms.rate_calendar (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    room_type_id     BIGINT        NOT NULL REFERENCES pms.room_types (id),
    date             DATE          NOT NULL,
    price            NUMERIC(10,2) NOT NULL CHECK (price > 0),
    source           VARCHAR(15)   NOT NULL
                     CHECK (source IN ('ML_MODEL', 'MANUAL', 'BASE', 'BASE_FALLBACK')),
    demand_indicator SMALLINT      CHECK (demand_indicator BETWEEN 0 AND 100),
    model_version    TEXT,
    factors          JSONB,
    computed_at      TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT uq_rate_calendar_room_type_date UNIQUE (room_type_id, date)
);

COMMENT ON COLUMN pms.rate_calendar.price IS
    'BAR (Best Available Rate) for the room type and night; RatePlan prices are derived as BAR * price_modifier at read time.';
