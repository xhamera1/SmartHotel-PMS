# ADR-0009: PLN, Kraków location, Europe/Warsaw business time

- **Status:** Accepted
- **Date:** 2026-09-05
- **Deciders:** Patryk Chamera
- **Plan reference:** D16

## Context and Problem Statement

Currency, hotel location, and time semantics were unspecified. Ambiguity here
causes silent bugs (wrong “today”, DST mistakes, float money) and weakens the
event-intelligence story (distance-to-hotel, Ticketmaster geography).

## Considered Options

1. Multi-currency + UTC-only business dates
2. PLN only; fixed offset UTC+2 year-round; generic city centre
3. PLN only; IANA `Europe/Warsaw`; concrete Kraków hotel coordinates; grosz precision

## Decision Outcome

**Chosen option:** option 3, with these bindings:

| Concern | Decision |
|---|---|
| Currency | **PLN only** — `NUMERIC(10,2)` / `BigDecimal` / `Decimal`; **2 decimal places (grosz) everywhere**, including ML quote output |
| UI locale | **`pl-PL`** (dates and currency formatting) |
| Hotel city | **Kraków** |
| Hotel coordinates | **`50.068369, 19.924854`** (pond island in a Kraków park — event distance origin) |
| Event search radius | **15 km** (default; configurable) |
| Business dates | `DATE` columns, hotel-local calendar, no timezone on the value |
| “Today” / night-audit | IANA zone **`Europe/Warsaw`** |
| Audit timestamps | `TIMESTAMPTZ` stored in **UTC** |
| Stay | half-open **`[check_in, check_out)`** (ADR language: Stay / HotelNight) |

**CEST note:** `Europe/Warsaw` observes DST. In summer it is **CEST = UTC+2**;
in winter **CET = UTC+1**. The project never hardcodes `+02:00` — the zone
database applies the correct offset for each instant. Containers and CI set
`TZ=Europe/Warsaw` so “business today” matches the hotel.

### Consequences

- Good: one clear monetary and geographic story for the thesis demo.
- Good: DST handled correctly without manual offset logic.
- Bad / risk: single-currency limits internationalisation — out of thesis scope.
- Bad / risk: confusing CEST with a fixed +2 offset — mitigated by this ADR and
  using only the IANA zone name in config/code.

## More Information

Env: `HOTEL_LAT`, `HOTEL_LON`, `TZ` / `EVENT_RADIUS_KM` in `.env.example`.
Related: glossary (HotelNight, Stay), ADR-0001.
