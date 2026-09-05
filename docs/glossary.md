# Domain Glossary — Ubiquitous Language

The canonical vocabulary for SmartHotel-PMS. Every term below has **exactly one
meaning**, used consistently across database schemas, Java and Python code, API
contracts, tests, documentation, and the thesis text.

Rules of use:

1. If a concept is not named here, it does not have an agreed name yet — add it
   here (via PR) before using it in code.
2. Renaming a term requires updating this file and all representations in the
   same change.
3. UI copy may use friendlier synonyms (e.g. "booking"), but identifiers in
   code, schemas, and APIs always use the canonical term.

## Naming & unit conventions

| Context | Style | Example |
|---|---|---|
| Java classes / records | PascalCase | `RateCalendarEntry`, `PriceSource` |
| Java fields, JSON API properties | camelCase | `checkIn`, `demandIndicator`, `roomTypeCode` |
| Python modules, functions, columns | snake_case | `event_impact_score`, `daily_demand` |
| SQL tables & columns | snake_case | `rate_calendar`, `check_in` |
| Enum values (DB, JSON, code) | UPPER_SNAKE strings | `ML_MODEL`, `CHECKED_IN`, `BASE_FALLBACK` |

- **Money:** PLN only. `NUMERIC(10,2)` in PostgreSQL, `BigDecimal` in Java,
  `Decimal` in Python. Never floats.
- **Business dates** (hotel nights, check-in/out): plain ISO `YYYY-MM-DD`
  strings in APIs, `DATE` columns in the database, interpreted in the hotel's
  local calendar (Europe/Warsaw). No timezone arithmetic on business dates.
- **Audit timestamps** (`created_at`, `computed_at`, …): `TIMESTAMPTZ`, stored
  in UTC, ISO-8601 in APIs.

---

## Core terms

### Room

A physical, individually bookable hotel room identified by its `room_number`
(e.g. `204`). Every Room belongs to exactly one RoomType and has an operational
status: `AVAILABLE` or `OUT_OF_SERVICE`.

- Guests never choose a specific Room — they book a RoomType; the system
  assigns a concrete free Room at reservation time.
- Represented by: `pms.rooms`, Java `Room`.

### RoomType

The sellable category of rooms (e.g. `STD_DOUBLE` — "Standard Double"): unique
`code`, display name, description, `capacity` (max guests), `base_price`,
`min_price`, `max_price`, and `amenities`.

- **All pricing happens at RoomType level**, never per individual Room.
- The guest-facing product is a **(RoomType, RatePlan)** pair — see RatePlan.
- Invariant: `min_price <= base_price <= max_price`. Dynamic prices are always
  clamped into `[min_price, max_price]`.
- Represented by: `pms.room_types`, Java `RoomType`.

### RatePlan

The commercial terms a RoomType is sold under — e.g. `FLEX` (fully refundable),
`NONREF` (cheaper, non-refundable), `BB` (breakfast included). The sellable
product is always a (RoomType, RatePlan) pair.

- A RatePlan's nightly price is **derived**, never independently computed:
  `BAR × price_modifier`, rounded to grosz (e.g. NONREF = BAR × 0.90). Dynamic
  (ML) pricing operates only on the BAR — rate plans never touch the model
  (ADR-0007).
- `refundable` drives guest cancellation rights: guests may self-cancel only
  refundable reservations; admins can always cancel.
- Represented by: `pms.rate_plans`, Java `RatePlan`.

### Guest

The person a Reservation is for. Minimal PII by design: first/last name, email,
phone. Guests have **no user account and no password** — the public booking flow
is guest checkout, and later access to a Reservation uses confirmation code +
email. Deduplicated by email at booking time.

- Not to be confused with **StaffUser** (hotel employee with a login and an
  `ADMIN` or `RECEPTIONIST` role).
- Represented by: `pms.guests`, Java `Guest`.

### Reservation

A booking of exactly one Room for one Guest over one Stay, sold under one
RatePlan. The domain centerpiece. Carries a unique **confirmation code**, party size (`adults`),
`total_price` with a per-night `price_breakdown` snapshot, an origin channel
(`WEB` public booking or `ADMIN` panel), and a lifecycle status:

`CONFIRMED → CHECKED_IN → CHECKED_OUT`, with terminal branches
`CONFIRMED → CANCELLED` and `CONFIRMED → NO_SHOW` (set by the night-audit job).

- Two Reservations in an *active* status (`CONFIRMED`, `CHECKED_IN`) may never
  overlap on the same Room — enforced by a PostgreSQL exclusion constraint on
  (`room_id`, Stay), not just by application code.
- The price shown at booking time is the price charged, forever — the snapshot
  in `price_breakdown` (per-night price + PriceSource) makes it auditable.
- Represented by: `pms.reservations`, Java `Reservation`.

### Stay

The half-open date interval **`[check_in, check_out)`** of a Reservation:
check-in date *inclusive*, check-out date *exclusive*.

- Number of nights = `check_out - check_in`; `check_out > check_in` always
  (a zero-night stay is invalid).
- Half-open semantics make **same-day turnover** correct by construction: a
  stay ending on a date and another beginning on that same date do *not*
  overlap — the room turns over that day.
- Represented in the database as a generated `daterange(check_in, check_out,
  '[)')` column named `stay`, which feeds the no-double-booking exclusion
  constraint. Application code always works with the `check_in`/`check_out`
  pair; the range column is database-managed.

### HotelNight

The atomic unit of selling and pricing: one calendar date `d`, meaning
occupancy of a room from day `d` to day `d+1` in hotel-local time. A Stay
`[check_in, check_out)` consumes the HotelNights `check_in` … `check_out − 1`.

- The check-out date is **never** a HotelNight of that stay and is never
  charged.
- Everything nightly is keyed by HotelNight: RateCalendarEntry, DemandIndicator,
  occupancy metrics.
- Represented by: `DATE` columns (e.g. `rate_calendar.date`,
  `daily_demand.date`), plain `YYYY-MM-DD` in APIs.

### RateCalendarEntry

The precomputed **BAR** for one (RoomType, HotelNight) pair — the *only* place
the booking path reads prices from. Written by the nightly pricing refresh (or
a manual "refresh now" / admin override), never computed synchronously during a
guest request. RatePlan prices are derived from the BAR at read time via the
plan's `price_modifier`; the calendar stores only the BAR.

- Fields: price, PriceSource, DemandIndicator, `model_version`, `factors`
  (explanation payload), `computed_at`. Unique per (`room_type_id`, `date`).
- If no entry exists for a requested night, the RoomType `base_price` is used
  and the response flags it — availability search never fails for lack of a
  calendar entry.
- A `MANUAL` entry survives automated refreshes until the admin clears it.
- Represented by: `pms.rate_calendar`, Java `RateCalendarEntry`.

### PriceSource

The provenance of a price — every nightly price in the system carries one:

| Value | Meaning |
|---|---|
| `ML_MODEL` | Recommended by the pricing model (clamped to min/max), delivered by the pricing service |
| `MANUAL` | Set by an admin as an explicit override; wins over automated refreshes |
| `BASE` | RoomType `base_price`; no dynamic recommendation exists for that night (e.g. before ML integration or beyond the pricing horizon) |
| `BASE_FALLBACK` | Dynamic pricing was *attempted* but the pricing service was unavailable or returned an invalid response; `base_price` used instead — logged and surfaced in the admin UI |

- `BASE` is a normal state; `BASE_FALLBACK` is a resilience event worth
  noticing. The distinction is what makes the "pricing service down, bookings
  still work" behaviour observable and testable.
- Persisted in RateCalendarEntry and snapshotted per night into a
  Reservation's `price_breakdown`.

### DemandIndicator

An integer **0–100** per HotelNight expressing expected demand pressure from
local events: 0 = no event signal, 100 = exceptional demand (e.g. a stadium
concert plus a city-wide conference). Computed in the pricing service by
aggregating the EventImpactScores of events affecting that night.

- Consumed as a feature by the pricing model and displayed in the admin rate
  calendar so staff can see *why* a price is elevated.
- Represented by: `pricing.daily_demand` (canonical, with `top_event_ids`),
  copied onto `pms.rate_calendar.demand_indicator` for display.

### EventImpactScore

An integer **0–100** assigned to a *single* external event (concert, match,
conference…) by the Gemini LLM, estimating that event's impact on hotel booking
demand. Stored with its `confidence`, the list of `affected_nights` (an event
can influence the nights before/after it), a short natural-language
`rationale`, the LLM model + prompt version, and the raw response for audit.

- `is_fallback = true` marks scores produced by the deterministic heuristic
  used when the LLM is unavailable — fallback scores are real data, but
  distinguishable in analysis.
- One event has one current score; many scored events aggregate into one
  DemandIndicator per night.
- Represented by: `pricing.event_scores`.

---

## Supporting terms

| Term | Meaning |
|---|---|
| **BAR (Best Available Rate)** | The dynamically priced nightly price of a RoomType *before* rate-plan modifiers — what the ML model recommends and the rate calendar stores |
| **StaffUser** | Hotel employee account (`ADMIN` or `RECEPTIONIST`) with login credentials; the only authenticated actors in the system |
| **ConfirmationCode** | 8-character code from an unambiguous alphabet (no `0/O`, `1/I/l`), unique per Reservation; with the guest's email it authorizes lookup and cancellation |
| **PriceBreakdown** | JSONB snapshot on a Reservation: per-night price + PriceSource at booking time; the audit trail for "what was charged and why" |
| **NightAudit** | Scheduled job that closes each hotel day: marks `CONFIRMED` reservations with a missed check-in as `NO_SHOW` |
| **Event** | An external happening fetched from an event provider (Ticketmaster), deduplicated by (`provider`, `external_id`); input to LLM scoring |
| **ModelVersion** | Identifier of a trained pricing-model artifact in the model registry; stamped onto every prediction and RateCalendarEntry it produced |
| **Availability** | The answer to "which RoomTypes have a free Room for Stay S and party size N", with nightly prices joined from the rate calendar |

## Preferred terms — say this, not that

| Avoid | Use instead |
|---|---|
| booking (in code/schema/API) | **Reservation** (UI copy may say "booking") |
| customer, client, user (for the person staying) | **Guest** |
| user (for staff) | **StaffUser** |
| date range, period (of a reservation) | **Stay** |
| day, date (as the unit being priced/sold) | **HotelNight** |
| rate (alone), fee, cost | **BAR** (a room type's nightly price), **RatePlan** (the product dimension), or **price** |
| demand score / event score (interchangeably) | **DemandIndicator** (per night) vs **EventImpactScore** (per event) |
