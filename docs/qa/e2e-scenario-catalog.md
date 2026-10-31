# Katalog scenariuszy E2E (Phase 9)

**Cel:** udokumentować automatyczne ścieżki użytkownika Playwright przeciwko
pełnemu stackowi Docker (`compose` profile `app` + `stubs`) — materiał do
rozdziału testów w pracy inżynierskiej oraz kontrakt dla implementacji w `e2e/`.

**Stack:** frontend `:8088`, PMS `:8080`, pricing `:8081`, `EVENT_PROVIDER=static`,
model fixture, `TZ=Europe/Warsaw`, UI `pl-PL`.

**Kontrolki:** `data-testid` wg `frontend/src/shared/ui/testids.ts` (daty ISO w
polach `type="date"`, bez klikania w kalendarz MUI).

**Tagi Playwright:**
- `@smoke` — E2E-01, E2E-07, E2E-10 (PR / `main.yml`)
- `@fault` — E2E-10 (projekt `fault`, `workers: 1`)
- `@quarantine` — tylko po 2 nieuzasadnionych flakach (patrz `e2e-flake-policy.md`)

**Stability bar:** suite musi przejść **3 kolejne** zielone przebiegi CI zanim
zostanie required check na `main`.

---

## E2E-01 — Guest books a room `@smoke`

| | |
|--|--|
| **Cel** | Pełna ścieżka rezerwacji gościa; recepcja widzi wynik |
| **Preconditions** | Seed: dostępny typ pokoju (np. `STD`) + wolny pokój; daty `+35…+37` dni |
| **Steps** | 1. `/booking` — wypełnij `search-check-in` / `search-check-out` / `search-guests`, `search-submit` 2. Wybierz `select-rate-STD-FLEX` (lub dostępny FLEX) 3. Checkout: gość + `mock-payment-authorize` + `confirm-booking` 4. Admin `/admin/reservations` — wiersz z kodem |
| **Expected** | `confirmation-code` widoczny; `reservation-row-{code}` w adminie |
| **Isolation** | Unikalny email gościa (`e2e01-{worker}-{uuid}@example.com`) |

## E2E-02 — Sold-out dates

| | |
|--|--|
| **Cel** | Brak dostępności przy pełnym obłożeniu |
| **Preconditions** | API: dla wybranego typu i nocy zarezerwować **wszystkie** sellable rooms |
| **Steps** | Search na te same daty |
| **Expected** | `availability-empty` (lub brak `room-type-card-*`) |
| **Isolation** | Dedykowany room-type `E2S{worker}` z 1 pokojem + 1 rezerwacja |

## E2E-03 — Double-booking race (409)

| | |
|--|--|
| **Cel** | Przyjazny recovery przy wyścigu o ostatni pokój |
| **Preconditions** | Typ z **1** wolnym pokojem; gość w UI na checkout |
| **Steps** | 1. UI: search → select → checkout form filled 2. API: public `POST /api/v1/reservations` bierze ostatni pokój 3. UI: `confirm-booking` |
| **Expected** | `checkout-error` / problem 409; bez fałszywego confirmation |
| **Isolation** | Room-type `E2R{worker}` |

## E2E-04 — Guest cancel

| | |
|--|--|
| **Cel** | Anulowanie po kodzie + emailu |
| **Preconditions** | API: CONFIRMED refundable (`FLEX`), `check_in` ≥ dziś (Warsaw) |
| **Steps** | `/booking/manage` → code/email → `cancel-booking` → `cancel-confirm-submit` |
| **Expected** | `cancel-success`; brak ponownego `cancel-booking` |
| **Isolation** | Unikalny kod z API create |

## E2E-05 — Admin room-type CRUD → public search

| | |
|--|--|
| **Cel** | CRUD typu pokoju widoczny w wyszukiwarce |
| **Preconditions** | Admin storageState |
| **Steps** | `/admin/room-types` utwórz typ `E2T{worker}` + room; public search |
| **Expected** | `room-type-card-E2T{worker}` w wynikach |
| **Isolation** | Unikalny code typu |

## E2E-06 — Reservation lifecycle

| | |
|--|--|
| **Cel** | check-in → check-out; nielegalne akcje niedostępne |
| **Preconditions** | API: CONFIRMED z `check_in` = dziś (Warsaw) |
| **Steps** | Drawer: `reservation-action-check-in` → `reservation-action-check-out` |
| **Expected** | Statusy zgodne; po check-out brak check-in; cancel niedostępny w CHECKED_OUT |
| **Isolation** | Unikalna rezerwacja |

## E2E-07 — Manual override survives refresh `@smoke`

| | |
|--|--|
| **Cel** | MANUAL wygrywa z ML i zostaje po Refresh |
| **Preconditions** | Admin; komórka `rate-cell-{date}` |
| **Steps** | Override `override-price` → `refresh-prices` |
| **Expected** | Komórka nadal MANUAL / cena override |
| **Isolation** | Data +30 dni, typ STD |

## E2E-08 — Refresh prices updates guest price

| | |
|--|--|
| **Cel** | Refresh aktualizuje kalendarz; gość widzi nową cenę |
| **Preconditions** | Pricing UP (fixture model); komórka nie-MANUAL |
| **Steps** | Zapamiętaj cenę → `refresh-prices` → guest search |
| **Expected** | Komórka / oferta gościa odzwierciedla źródło MODEL/BASE (nie crash) |
| **Isolation** | Unikalny zakres dat |

## E2E-09 — Auth role matrix

| | |
|--|--|
| **Cel** | Anonim → login; RECEPTIONIST bez settings |
| **Steps** | 1. `/admin/reservations` bez sesji → `/admin/login` 2. Login reception → `/admin/room-types` zabronione |
| **Expected** | Redirect login; brak `admin-room-types` / redirect away |
| **Isolation** | `reception@smarthotel.local` storageState |

## E2E-10 — Pricing down fallback `@smoke` `@fault`

| | |
|--|--|
| **Cel** | Booking przy wyłączonym pricing; admin widzi banner fallback |
| **Preconditions** | `docker stop smarthotel-pricing` |
| **Steps** | Guest book → confirmation; admin rate calendar |
| **Expected** | Booking OK; po `refresh-prices` PMS zwraca `status=DEGRADED` → `pricing-fallback-banner` (lub komórki `BASE_FALLBACK`) |
| **Teardown** | `docker start smarthotel-pricing` + wait healthy |
| **Isolation** | Serial project; nie równolegle z innymi |

## E2E-11 — Events view

| | |
|--|--|
| **Cel** | Lista eventów ze score i rationale |
| **Preconditions** | Static sync / seed `daily_demand` (compose start lub `POST …/internal/events/sync`) |
| **Steps** | `/admin/events` — zakres dat pokrywający fixture static (np. 2027-04…2027-10) |
| **Expected** | `events-table` z wpływem i uzasadnieniem; demand section niepusta |
| **Isolation** | Read-only względem współdzielonych fixture’ów |

---

## Macierz tagów CI

| Job | Filter |
|-----|--------|
| PR / main smoke | `--grep @smoke` |
| Nightly full | all except optional `@quarantine` |
| Fault | project `fault` (E2E-10 only) |

## Artefakty pracy inżynierskiej

- Ta tabela scenariuszy
- Trace Viewer (Playwright) po flaku / retry
- Opis polityki flake (`e2e-flake-policy.md`)
