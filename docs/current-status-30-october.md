# SmartHotel-PMS — status projektu (30 października 2026)

**Werdykt:** produktowo jesteśmy po **fazach 0–9** (Playwright E2E-01…11 + fault), z domknięciem luk z §5 (Must/Should/Nice) z 30.10.2026 (DEF-0006…0016). Przed nami głównie **fazy 10–14** (pełne dashboardy Kibana, k6, `compose.demo.yml`, eksperymenty, demo obrony). Compose ma już frontend + profile `stubs`/`observability` (MVP).

**Założenie obciążenia (audit):** jeden hotel, kilku pracowników + goście bookingowi, nocny batch cen — nie multi-property SaaS.

---

## 1. Jak weryfikowano

| Źródło | Co zrobiono |
|--------|-------------|
| Plan | `docs/detailed_implementation_plan.md` (fazy 0–14) — **nie traktowany jako źródło prawdy**; każdy punkt sprawdzany w kodzie |
| Kod | `services/pms-core`, `services/pricing-service`, `frontend`, `infra`, `.github/workflows`, `docs/`, `artifacts/` |
| Runtime | Docker Desktop → PostgreSQL (`profile core`) healthy; lokalnie uruchomione **pms-core :8080**, **pricing-service :8081**, **Vite frontend :5173** |
| API smoke (live) | login, availability, booking + lookup + cancel, dashboard, rate-calendar, pricing refresh, admin events, quotes, model, events sync |
| Testy (po remediation) | Java unit: **88/88 OK**; Python: **194 passed**; frontend Vitest: **33/33 OK** |
| Audyty kodu (równolegle) | Pogłębione przeglądy `pms-core`, `pricing-service`, frontend/CI/infra — ustalenia włączone poniżej (§5, §7, §8) |

Szczegóły lokalnego odpalania: też w `docs/weryfikacja-lokalna.md` (częściowo nadal aktualne).

---

## 2. Etap względem planu (fazy 0–14)

Legenda: ✅ zrobione i potwierdzone · 🟡 częściowo / drobne luki · ❌ nie rozpoczęte lub tylko placeholder

| Faza | Plan | Status | Komentarz |
|------|------|--------|-----------|
| **0** Bootstrap | monorepo, Taskfile, compose, CI, ADR, defect journal | ✅ | Repo, toolchain, `.gitattributes`, ADRy, `pr.yml` |
| **1** Domain / DB / kontrakty | Flyway + Alembic, ERD, glossary, OpenAPI docs | ✅ | Schematy `pms`/`pricing`, diagramy, `docs/api/*`, glossary |
| **2** PMS Core | rezerwacje, auth, availability, night-audit, rate calendar | ✅ (+ ekstra rate plans) | Pełne API admin/public; exclusion constraint; race IT; ArchUnit; bucket4j login limit |
| **3** Frontend | booking + admin, MUI, TanStack, OpenAPI types | ✅ | Flowy + Vitest; compose `app` ma nginx SPA (`task up:app`, port 8088) |
| **4** Datagen + EDA | generator, pandera, notebook/figures | ✅ | Datasets + committed `golden_hashes.json`; EDA `default` nadal opcjonalne |
| **5** ML train / eval | RF, baselines, ablation, gate, metamorphic | ✅ | Metamorphic preferuje fixture (canary) + synthetic fallback; test shipped fixture predict |
| **6** Pricing API | FastAPI quotes/health/model, OpenAPI drift | ✅ | Fail-fast schema mismatch; quote features z `top_event_ids` + scores |
| **7** Events + Gemini | Ticketmaster/static, scoring, fallback, demand | ✅ | Sync fixed; pin `gemini-2.5-flash`; fuzzy-dedupe nadal nice-to-have |
| **8** Integracja PMS↔pricing | Resilience4j, refresh, proxy, fallback | ✅ | Proxy mapuje confidence/rationale; horyzont default 180 |
| **9** E2E Playwright | E2E-01…11 + fault injection | ✅ | `e2e/` + katalog/flake policy; CI smoke `@smoke` + nightly full; required check po 3× green |
| **10** Observability ELK | ES + Kibana + Filebeat | 🟡 | Compose profile `observability` + `filebeat.yml` MVP; brak Kibana dashboards ndjson |
| **11** Perf k6 | smoke/load/soak + baselines | ❌ | Tylko `perf/README.md` |
| **12** CI/CD hardening | Trivy, gitleaks, GHCR, release | 🟡 | GHCR + frontend image; Dependabot; Trivy exit 1; brak `compose.demo.yml` / RELEASE |
| **13** Eksperymenty RQ1–4 | protokoły + `task experiments` | 🟡 | `docs/qa/experiment-protocols.md` pre-registered; ablation artifacts istnieją |
| **14** Demo / obrona | `compose.demo.yml`, skrypt demo, traceability | ❌ | Częściowo: seed + static provider + fixture model; brak demo compose / backup video / macierzy wymagań |

**Najkrótsza odpowiedź „gdzie jesteśmy”:** skończony **track A + track B + integracja + E2E (Phase 8–9)**. Następny duży kamień milowy: **Phase 10–11 (ELK dashboards / k6)** oraz materiały Phase 13/14 pod dyplom.

---

## 3. Co już mamy (potwierdzone w kodzie + runtime)

### 3.1 Infrastruktura i governance
- Monorepo zgodny z §4.3 planu; PostgreSQL 17 z izolacją schematów `pms` / `pricing` i `btree_gist`
- `task up` / smoke DB OK (schemas, users, extension)
- 14 ADR-ów (`0001`–`0014`), w tym rozszerzenie względem planu: **rate plans od BAR** (`0007`)
- Defect journal z realnymi wpisami (DEF-0001…), test strategy, dataset-spec
- Kolekcja Postman: `Smart-Hotel-PMS-Collection.postman_collection.json`

### 3.2 pms-core (Java 21 / Spring Boot 3.4)
**Zaimplementowane endpointy (zweryfikowane w kontrolerach):**
- Public: availability, create reservation, lookup, cancel
- Auth: login / refresh / logout (+ rate limit)
- Admin: room-types, rooms, guests, reservations (+ check-in/out/cancel/no-show), rate-calendar, rate-plans, dashboard KPIs/timeseries
- Pricing seam: `POST /admin/pricing/refresh`, `GET .../events`, `GET .../demand-indicators`

**Jakość:**
- Stan maszyny rezerwacji + night-audit job
- Double-booking: constraint DB + `DoubleBookingRaceIT`
- `PricingClient` + Resilience4j + `BASE_FALLBACK`
- Scheduled rate-calendar refresh (03:00 Europe/Warsaw)
- Testy: unit 88 OK; IT m.in. SecurityMatrix, DoubleBookingRace, CrossService, RateCalendar, Auth, OpenAPI export

### 3.3 pricing-service (Python 3.12 / FastAPI)
- Quotes batch, demand, events, model info, health live/ready, internal reload/sync
- Datagen CLI + walidacja; trening RF; registry/promote; ML gate; metamorphic tests
- Events: StaticFile + Ticketmaster port, Gemini + heuristic fallback, aggregation → `daily_demand`
- Fixture model do lokalnego/demo startu (`ALLOW_FIXTURE_MODEL`)
- Artefakty: datasets, modele, EDA, ablation comparison

### 3.4 Frontend (React / Vite / MUI)
- Public booking: search → checkout → confirmation → manage
- Admin: dashboard, reservations, guests, rate calendar, events; room-types/rooms tylko `ADMIN`
- Auth guards, i18n (PL — *could-have* z planu, już jest), theme, OpenAPI types, MSW + Vitest (**29** testów, coverage ~89% na mierzonym zakresie)

### 3.5 CI
- `pr.yml`: paths-filter, java verify, python (+ openapi drift, schemathesis, ml-gate), frontend
- `integration.yml` / `main.yml`: compose `app`, refresh kalendarza, booking po `docker stop` pricing
- `live-smoke.yml`, `nightly.yml` — szkielety pod dalsze fazy

---

## 4. Smoke runtime (30.10.2026) — co działa dobrze

| Check | Wynik |
|-------|-------|
| Postgres smoke | OK |
| Alembic `pricing` | OK (z `PRICING_DATABASE_URL` z `.env`) |
| PMS `/actuator/health` | UP |
| Pricing `/health/live` + `/ready` | OK (model fixture) |
| `GET /api/v1/model` | OK |
| `POST /api/v1/quotes` (z `requestId`) | OK — np. price 414, multiplier ~1.18 |
| `POST /internal/events/sync` (static) | OK → 7 events, 22 demand days |
| PMS login admin | OK |
| Availability | OK — ceny z `priceSource: ML_MODEL` po refresh |
| Booking STD/FLEX | OK — np. `FY5JRXDE`, total 528 PLN, CONFIRMED |
| Lookup | OK |
| Cancel `?email=` | OK → CANCELLED |
| Admin dashboard / room-types / rate-calendar | OK — source `ML_MODEL` |
| `POST /admin/pricing/refresh` | OK |
| Admin proxy events | OK |
| Frontend http://127.0.0.1:5173 | 200 |

**Uwagi kontraktowe przy smoke (nie „dziury produktu”, tylko precyzja API):**
- Quotes **wymaga** `requestId` (UUID) + `currency`
- Create reservation **wymaga** `ratePlanCode` (FLEX / NONREF / BB)
- Cancel bierze `email` jako **query param**, nie body

---

## 5. Co należy poprawić (teraz / wkrótce)

**Stan po remediation 30.10.2026:** punkty 1–17 z listy Must/Should/Nice **zamknięte** (DEF-0006…0016).  
Pozostałe luki produktowe: Phase 9 Playwright, Kibana dashboards ndjson, k6, `compose.demo.yml`, fuzzy event dedupe.

### Zamknięte (Must)
1. ~~2 padające testy Pythona~~ → DEF-0006, DEF-0007  
2. ~~README Project status~~ → DEF-0008  

### Zamknięte (Should)
3. ~~Frontend w compose `app`~~ → DEF-0014 (`task up:app`)  
4. ~~Profile stubs / observability~~ → DEF-0014 (MVP WireMock + ES/Kibana/Filebeat)  
5. ~~`task seed` vs Flyway~~ → DEF-0013  
6. ~~`experiment-protocols.md`~~  
7. ~~Postman Phase 8 smoke~~  
8. ~~Events proxy confidence/rationale~~ → DEF-0009  
9. ~~Quote event features~~ → DEF-0010  
10. ~~`golden_hashes.json`~~ → DEF-0011  
11. ~~Fail-fast model schema~~ → DEF-0012  

### Zamknięte (Nice)
12. ~~RTL SearchForm + rate-calendar cell sources~~  
13. ~~Metamorphic + fixture canary / shipped predict~~  
14. ~~Horizon default 180~~ (ścieżki `/admin/pricing/*` celowo zostawione) → DEF-0016  
15. ~~OpenApiConfig opis~~  
16. ~~Gemini pin `gemini-2.5-flash`~~ → DEF-0015  
17. ~~Trivy exit 1, Dependabot, frontend GHCR~~

---

## 6. Co należy dodać / co przed nami

### Phase 9 — E2E ✅
- ~~Scaffold Playwright w `e2e/`~~ + `docs/qa/e2e-scenario-catalog.md` / flake policy
- ~~Scenariusze E2E-01…11~~ (booking, sold-out, race 409, cancel, CRUD, lifecycle, override, refresh, auth, kill pricing, events)
- ~~CI `main` smoke + `nightly` full (`app`+`stubs`, `EVENT_PROVIDER=static`)~~; required check dopiero po 3× green
- Fallback banner: `pricing-fallback-banner` + PMS refresh `DEGRADED` gdy 0 upsertów
- ~~Job smoke/full~~ w `main.yml` / `nightly.yml` (`app+stubs`); required check po 3× green

### Phase 10 — Observability
- Compose profile `observability` MVP już jest (ES/Kibana/Filebeat)
- Domknięcie JSON logs + correlation E2E; dashboards ndjson w `infra/elk/`

### Phase 11 — Performance
- Seed perf (~100k reservations) w `infra/seed/perf`
- Scenariusze k6 + baselines; smoke w CI

### Phase 12 — Domknięcie delivery
- Trivy fail HIGH+, Dependabot, frontend GHCR — zrobione
- `compose.demo.yml` z pinami; ASVS-lite + RELEASE.md
- Mutation testing = Optional-Advanced

### Phase 13 — Badania dyplomowe
- Pre-register `experiment-protocols.md` — zrobione
- E1–E4: pełne tabele/wykresy do rozdziałów wyników (część ablation już jest)
- Analiza defect journal pod RQ4
- Live Gemini eval tylko poza CI (`live-smoke`)

### Phase 14 — Obrona
- Narracyjny seed „weekend koncertowy w Krakowie”
- Demo script 10 min + backup video
- Traceability matrix opis ↔ kod ↔ testy
- Fresh-machine clone → demo

---

## 7. Porównanie plan ↔ rzeczywistość (świadome odchylenia)

| Temat | Plan | Faktycznie |
|-------|------|------------|
| Rate plans | nie w early scope szczegółowo | **Zaimplementowane** (FLEX/NONREF/BB, ADR-0007) — booking wymaga `ratePlanCode` |
| Frontend w compose `app` | tak | **nie** — tylko pms-core + pricing-service |
| WireMock stubs profile | tak | placeholder |
| ELK | Phase 10 | brak usług; brak `logstash-logback-encoder` / `structlog` w grepie usług |
| i18n | could-have | **jest** (PL messages) |
| Login rate limit | Optional-Advanced | **jest** (bucket4j) |
| Node / Spring | Node 24, SB 3.x | zgodne (SB 3.4.4) |
| Refresh URL | `POST /admin/rate-calendar/refresh` | `POST /api/v1/admin/pricing/refresh` |
| Events/demand admin | `/admin/events`, `/admin/demand-indicators` | `/api/v1/admin/pricing/events`, `.../demand-indicators` |
| Rate calendar key | `{roomTypeId}` | `{roomTypeCode}` |
| Refresh horizon | 180 dni | **365** (`PRICING_REFRESH_HORIZON_DAYS`) |
| Pricing retry | ×2 | **3** attempts w `application.yml` |
| Dashboard | tylko KPIs | + `timeseries` (occupancy/ADR) |
| Structured JSON logs | Phase 10 day-one fields | correlation ID jest; pełny ELK schema stack jeszcze nie |

Plan nie jest „błędny” — jest baseline; kod w kilku miejscach **poszedł dalej** (rate plans, i18n, rate limit, timeseries) albo **jeszcze nie doszedł** (9–11, część 12–14).

---

## 8. Audit jakości (skrót, styl ponytail-audit)

**What this repo does:** PMS hotelowy z publicznym bookingiem i silnikiem dynamicznych cen (Random Forest + wskaźnik popytu z eventów/Gemini), w dwóch backendach + React SPA.

### Must fix
1. **Padające testy datagen/events** (`test_season_factor_bounded`, `test_sync_pipeline_with_mocked_deps`) — CI python będzie czerwone.
2. **Dokumentacja statusu** (README) wprowadza w błąd co do etapu.

### Should fix
3. ~~Brak E2E~~ — Phase 9 zrobione; required GitHub check dopiero po 3× green.
4. ~~Brak frontendu w compose~~ — profile `app` ma nginx SPA `:8088`.
5. Brak pre-registered experiment protocols przed dalszymi runami badawczymi (częściowo: `experiment-protocols.md`).
6. ~~Event proxy / quotes features~~ — domknięte w Phase 8 remediation.
7. ~~Datagen golden hashes~~ — committed.

### Nice to have
8. Więcej RTL na stronach admin; Postman Phase 8; metamorphic na shipped model; ELK gdy potrzebne do wykresów w pracy.

**Verdict:** zdrowy rdzeń produktowy po Phase 8–9; dalej Phase 10/11 + materiały Phase 13/14 pod dyplom.

**Not checked w tej sesji:** pełny `mvn verify` od zera (użyto świeżych unit + istniejących failsafe reports ~81 IT), live Ticketmaster/Gemini z prawdziwymi kluczami, pełny `docker compose --profile app` build obrazów, ręczne kliknięcie całego UI w przeglądarce (tylko HTTP 200 frontendu + API), testcontainers Python integration lokalnie.

---

## 9. Rekomendowana kolejność prac (najbliższe 2–4 sprinty)

1. Utrzymać E2E green ×3 w CI, potem required check na `main`.  
2. Phase 10: Kibana dashboards ndjson + pełny JSON log schema.  
3. Phase 11: k6 smoke/load/soak + baselines.  
4. Phase 13: regeneracja tabel E1/E2; E3 gdy klucze Gemini.  
5. Phase 14: `compose.demo.yml` + video zapasowe.

---

## 10. Konta / porty (przypomnienie z weryfikacji)

| Usługa | URL |
|--------|-----|
| PMS | http://localhost:8080 (Swagger: `/swagger-ui`) |
| Pricing | http://localhost:8081 (`/docs`, klucz `X-Internal-Api-Key`) |
| Frontend | http://localhost:5173 |
| Postgres | localhost:5432 |

Staff seed: `admin@smarthotel.local` / `admin-dev-password`, `reception@smarthotel.local` / `reception-dev-password`.

---

*Wygenerowano 30.10.2026 na podstawie planu, kodu, Docker Desktop oraz live smoke API/testów lokalnych.*
