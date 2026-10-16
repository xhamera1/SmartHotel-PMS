# Weryfikacja lokalna — SmartHotel-PMS (fazy 0–8)

Krótki przewodnik: co już działa, jak odpalić, jak sprawdzić API (Postman), ML i LLM.

---

## 1. Co działa / co jeszcze nie

| Obszar | Status | Jak sprawdzić |
|--------|--------|---------------|
| PostgreSQL + schematy `pms` / `pricing` | ✅ | `task up` → `task smoke` |
| **pms-core** (Spring) — rezerwacje, admin API, auth | ✅ | `task run:pms` → :8080 |
| **Frontend** (React) — booking + panel | ✅ | `task run:frontend` → :5173 |
| **Datagen** + EDA | ✅ | `task datagen` / notebook EDA |
| **ML** — trening RF, metrics gate, fixture model | ✅ | `task ml:train` / `GET /api/v1/model` |
| **pricing-service API** — quotes, health, model | ✅ | `task run:pricing` → :8081 |
| **Eventy** — static fixtures + heuristic scoring | ✅ | `task events:sync` (bez kluczy) |
| **Gemini + Ticketmaster** (live) | ✅ opcjonalnie | klucze w `.env` + `EVENT_PROVIDER=ticketmaster` |
| **Integracja PMS ↔ pricing** (rate calendar refresh) | ✅ Phase 8 | `POST /api/v1/admin/pricing/refresh` → `rate_calendar` |
| E2E Playwright, ELK, k6 | ❌ Phase 9–11 | — |

**Wniosek:** ML/LLM możesz nadal oceniać bezpośrednio na :8081; pełny flow cen w PMS to refresh kalendarza + booking.

---

## 2. Jednorazowa konfiguracja

```powershell
# z katalogu repo
Copy-Item .env.example .env   # jeśli jeszcze nie masz .env
# Wypełnij (opcjonalnie, do LLM/Ticketmaster):
#   GEMINI_API_KEY=...
#   TICKETMASTER_API_KEY=...
#   EVENT_PROVIDER=static   # zostaw static na start

task up
task db-migrate:pricing
task seed                  # użytkownicy staff + pokoje
```

**Porty (ważne):**
- PMS: `http://localhost:8080`
- Pricing: `http://localhost:8081` ← używaj tego w Postmanie
- Frontend: `http://localhost:5173`
- Swagger pricing: `http://localhost:8081/docs`

**Klucz API (pricing):** header `X-Internal-Api-Key: dev-internal-api-key`  
(z `.env` → `INTERNAL_API_KEY`)

**Logowanie staff (frontend / PMS):**
- `admin@smarthotel.local` / `admin-dev-password`
- `reception@smarthotel.local` / `reception-dev-password`

---

## 3. Uruchomienie „stacku do oglądania”

W osobnych terminalach:

```powershell
task up
task run:pms
task run:pricing
task run:frontend
```

Albo tylko pricing (wystarczy do ML/LLM/quotes):

```powershell
task up
task db-migrate:pricing
task run:pricing
```

Sprawdź zdrowie:
- `GET http://localhost:8081/health/live` → `{"status":"UP"}`
- `GET http://localhost:8081/health/ready` → model + DB OK

---

## 4. Postman — pełna kolekcja

Import: plik `Smart-Hotel-PMS-Collection.postman_collection.json` (Import → File).

Zawiera **wszystkie** endpointy PMS + pricing, zmienne (`pmsBaseUrl`, `pricingBaseUrl`, `internalApiKey`, konta seed), folder **00 — Quick smoke**, auto-zapis JWT po loginie.

### Pricing — kolejność ręczna

Ustaw zmienną kolekcji: `pricingBaseUrl = http://localhost:8081`, header na requestach (poza health):

| Header | Wartość |
|--------|---------|
| `X-Internal-Api-Key` | `dev-internal-api-key` |
| `Content-Type` | `application/json` |

### Krok A — model ML

`GET {{base}}/api/v1/model`

Oczekuj: `isReady: true`, `version`, metryki. To jest aktywny Random Forest (fixture albo wytrenowany).

### Krok B — wycena (ocena ML)

`POST {{base}}/api/v1/quotes`

```json
{
  "requestId": "11111111-1111-1111-1111-111111111111",
  "currency": "PLN",
  "items": [
    {
      "roomTypeCode": "STD",
      "date": "2027-06-14",
      "basePrice": 350.00,
      "minPrice": 250.00,
      "maxPrice": 700.00,
      "occupancyRate": 0.75,
      "roomsRemaining": 5,
      "leadTimeDays": 30
    },
    {
      "roomTypeCode": "DLX",
      "date": "2027-06-14",
      "basePrice": 420.00,
      "minPrice": 300.00,
      "maxPrice": 800.00,
      "occupancyRate": 0.85,
      "roomsRemaining": 2,
      "leadTimeDays": 14
    }
  ]
}
```

Patrz na: `price`, `multiplier`, `demandIndicator`, `factors.topSignals`.  
Zmień `occupancyRate` / `leadTimeDays` / datę — cena powinna się zmieniać sensownie.

### Krok C — sync eventów (LLM / heurystyka)

`POST {{base}}/internal/events/sync` → **202** Accepted  
Pipeline leci w tle (kilka sekund przy `static` + heurystyce).

Potem:
- `GET {{base}}/api/v1/events?from=2027-01-01&to=2027-12-31`
- `GET {{base}}/api/v1/demand-indicators?from=2027-01-01&to=2027-12-31`

Przy `EVENT_PROVIDER=static` i pustym `GEMINI_API_KEY` → **HeuristicScorer** (`is_fallback` w score’ach).  
Z kluczem Gemini → prawdziwy LLM (structured JSON).

### Live Ticketmaster + Gemini

W `.env`:

```env
EVENT_PROVIDER=ticketmaster
TICKETMASTER_API_KEY=...
GEMINI_API_KEY=...
```

Restart pricing → znowu `POST /internal/events/sync` → sprawdź `/events` i rationales.

CLI bez API:

```powershell
task events:sync
```

---

## 5. Jak ocenić model ML

| Metoda | Komenda / endpoint | Co patrzysz |
|--------|-------------------|-------------|
| Info runtime | `GET /api/v1/model` | wersja, MAE/RMSE jeśli zapisane |
| Quotes | `POST /api/v1/quotes` | multiplier, clamp do min/max, factors |
| Trening od zera | `task ml:train` | artefakt w `artifacts/models/` |
| Ablacja eventów | `task ml:ablation` | RF z/bez feature’ów eventowych |
| Gate regresji | `task ml:gate` | czy metryki nie posypały się vs baseline |
| Testy | `task test:python` | unit + API |

**Uwaga:** target to **mnożnik** względem `basePrice` (ADR-0010), nie absolutna cena „z kapelusza”.

---

## 6. Jak ocenić LLM (Gemini)

| Metoda | Gdzie | Co patrzysz |
|--------|-------|-------------|
| Notebook porównawczy | `services/pricing-service/notebooks/gemini_scoring_analysis.ipynb` | Gemini vs heurystyka, latency, stabilność, canary injection |
| Demo pipeline (bez klucza) | `notebooks/events_pipeline_demo.ipynb` | score’y, kalendarz popytu, injection blocked |
| Live smoke | `uv run pytest tests/events/test_live_smoke.py -m external` | prawdziwe API |
| Po syncu | `GET /api/v1/events` | `impactScore`, `rationale`, `confidence` |

**Obrona przed injection:** event `static-018` ma złośliwą nazwę — score **nie** powinien być 100 dla wszystkich.

Bez Gemini pipeline i tak działa (heurystyka) — to świadoma decyzja (ADR-0011).

---

## 7. Frontend / PMS (co da się kliknąć już teraz)

1. `http://localhost:5173` — booking gościa (availability → rezerwacja).
2. Panel admina — login staff (dane wyżej): pokoje, rezerwacje, rate calendar.
3. **Dynamic pricing w kalendarzu** — po loginie ADMIN: `POST /api/v1/admin/pricing/refresh`, potem `GET /api/v1/admin/rate-calendar`. Eventy/popyt: `GET …/pricing/events` i `…/demand-indicators`. Flaga `PRICING_ENABLED=false` wraca do cen bazowych.

Compose z oboma serwisami: `docker compose --env-file .env -f infra/compose.yml --profile app up -d --wait`.

---

## 8. Szybka checklista „czy wszystko żyje” (15 min)

1. `task up` + `task smoke`
2. `task run:pricing` → `/health/ready` = UP
3. `GET /api/v1/model` → `isReady`
4. `POST /api/v1/quotes` (body z §4) → ceny ≠ same basePrice przy wysokiej occupancy
5. `POST /internal/events/sync` → po chwili `GET /api/v1/events` niepuste
6. (opcjonalnie) notebook Gemini z kluczem
7. `task run:pms` + `task run:frontend` → booking + login admina

---

## 9. DataGrip — podłączenie do bazy

Najpierw: `task up` (kontener `smarthotel-postgres` musi działać).

### Połączenie (zalecane: superuser do oglądania obu schematów)

| Pole | Wartość |
|------|---------|
| Host | `localhost` |
| Port | `5432` (albo `POSTGRES_HOST_PORT` z `.env`) |
| Database | `smarthotel` |
| User | `postgres` |
| Password | `postgres-dev-password` |
| Driver | PostgreSQL |

W DataGrip: **+ → Data Source → PostgreSQL** → wklej powyższe → **Test Connection** → OK.

Na dole w Advanced / Options możesz ustawić `currentSchema=pricing` albo `pms`, ale wygodniej przeglądać schematy w drzewku po lewej (`smarthotel` → `schemas` → `pms` / `pricing`).

### Osobne user’y usług (opcjonalnie)

| User | Password | Widzi głównie |
|------|----------|---------------|
| `pms_user` | `pms-dev-password` | schema `pms` |
| `pricing_user` | `pricing-dev-password` | schema `pricing` |

Do weryfikacji eventów / ML logów wystarczy `postgres` albo `pricing_user`.

### Proste zapytania weryfikacyjne

Po `task seed` + `task db-migrate:pricing` + (opcjonalnie) `task events:sync` / quotes:

```sql
-- Schematy i tabele
SELECT schema_name FROM information_schema.schemata
 WHERE schema_name IN ('pms', 'pricing');

SELECT table_schema, table_name
  FROM information_schema.tables
 WHERE table_schema IN ('pms', 'pricing')
 ORDER BY 1, 2;

-- PMS: pokoje / staff / rezerwacje
SELECT COUNT(*) AS rooms FROM pms.rooms;
SELECT email, role FROM pms.staff_users;
SELECT status, COUNT(*) FROM pms.reservations GROUP BY status;

-- Pricing: eventy po syncu
SELECT provider, status, COUNT(*) FROM pricing.events GROUP BY 1, 2;
SELECT external_id, name, category, distance_km, starts_at
  FROM pricing.events ORDER BY starts_at LIMIT 20;

-- Score’y (LLM lub heurystyka)
SELECT e.name, s.impact_score, s.confidence, s.is_fallback, s.rationale
  FROM pricing.event_scores s
  JOIN pricing.events e ON e.id = s.event_id
 ORDER BY s.impact_score DESC
 LIMIT 20;

-- Agregacja popytu
SELECT date, indicator, top_event_ids
  FROM pricing.daily_demand
 ORDER BY date
 LIMIT 30;

-- Model w rejestrze + ostatnie predykcje (po POST /quotes)
SELECT version, is_active, metrics FROM pricing.model_registry;
SELECT created_at, room_type_code, stay_date, predicted_price, multiplier
  FROM pricing.prediction_log
 ORDER BY created_at DESC
 LIMIT 20;
```

**Jak czytać wyniki:**
- puste `pricing.events` → nie było syncu (`POST /internal/events/sync` albo `task events:sync`)
- `is_fallback = true` → heurystyka (brak Gemini / fallback)
- `is_fallback = false` → Gemini
- puste `prediction_log` → jeszcze nie było udanego `POST /api/v1/quotes`
- puste `pms.rooms` → brak `task seed` (albo trzeba `task db-reset` + seed od zera)

---

## 10. Typowe problemy

| Objaw | Co zrobić |
|-------|-----------|
| `401` na quotes | Brak / zły `X-Internal-Api-Key` |
| `503` ready/quotes lub traceback `model_registry does not exist` | Brak migracji: `task db-migrate:pricing`, potem restart pricing (fixture ładuje się z `fixtures/models/tiny`) |
| `fixture model not found under artifacts\models` | Stary log — `MODEL_ARTIFACT_DIR` to katalog trenowanych modeli; fixture jest osobno. Zrób migrate + restart |
| Sync 202, ale puste events | Poczekaj / sprawdź logi uvicorn; DB migracje? |
| Gemini nie wołany | Pusty klucz lub budżet / circuit breaker → heurystyka |
| PMS na złym porcie pricing | Lokalnie pricing = **8081**, nie 8000 z przykładowego `PRICING_BASE_URL` |

---

## 11. Testy (pewność „co jest zielone”)

```powershell
cd services/pricing-service
uv run pytest -q -m "not integration and not benchmark and not external"
```

Live API (ręczne, z kluczami):

```powershell
uv run pytest tests/events/test_live_smoke.py -m external -v
```

---

*Stan na koniec Phase 7. Następny duży krok integracyjny: Phase 8 (PMS woła pricing i wypełnia rate calendar).*
