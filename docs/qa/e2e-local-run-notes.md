# E2E — lokalne uruchomienie i wnioski z diagnostyki (Phase 9)

Materiał pod rozdział testów / QA w pracy inżynierskiej: typowe „czerwone” przebiegi, które **nie** wskazują na błąd logiki aplikacji.

## Poprawna procedura

```bash
# 1) stack — zawsze z ROOT repo (tu leży .env)
cd ~/studia/inzynierka/SmartHotel-PMS
docker compose --env-file .env -f infra/compose.yml --profile app --profile stubs up -d --build --wait

# 2) Playwright
cd e2e
pnpm install
pnpm exec playwright install chromium   # lokalnie wystarczy Chromium
pnpm test                               # = chromium + fault (E2E-10)
pnpm test:smoke                         # @smoke na tych samych projektach
```

Firefox jest opcjonalny (parity z nightly CI):

```bash
pnpm exec playwright install firefox
pnpm test:firefox
```

## Incydent (2026-10-31) — 11 failed / 14 passed

### Objawy

- `docker compose … couldn't find env file: …/e2e/.env`
- `pnpm test -- --project=chromium --project=fault` uruchomił **25** testów (chromium + firefox + fault)
- Wszystkie failury: `[firefox] browserType.launch: Executable doesn't exist … firefox.exe`
- Chromium + fault: **zielone** (w tym E2E-10)

### Diagnoza (nie bug aplikacji)

| Objaw | Przyczyna | Warstwa |
|-------|-----------|---------|
| Brak `.env` | Compose odpalony z `e2e/`; ścieżka `--env-file .env` jest względna do CWD | DX / dokumentacja |
| Firefox w runie mimo `--project=chromium` | Pod Git Bash / pnpm literalne `--` trafia do CLI: `playwright test "--" "--project=…"` — filtry projektów nie działają jak oczekiwano, lecą **wszystkie** projekty z `playwright.config.ts` | DX / skrypty npm |
| Brak `firefox.exe` | Zainstalowano tylko `chromium`; projekt `firefox` i tak wystartował | Środowisko lokalne |

**Wniosek:** wynik nie dowodzi regresji PMS/frontu. Dowodzi potrzeby: (1) compose z roota, (2) skryptów npm z wbudowanym `--project`, (3) instalacji tylko tych przeglądarek, które się odpala.

### Naprawa w repo

- `e2e/package.json`: `test` / `test:smoke` domyślnie `--project=chromium --project=fault`
- `e2e/README.md`: CWD + skrypty bez problematycznego `pnpm test -- …`
- Ten plik: zapis pod pracę dyplomową

### Jak to opisać w pracy (skrót)

Przy testach E2E w monorepo z Docker Compose istotne jest rozróżnienie **failury produktu** od **failury harnessu** (ścieżki env, brak binariów przeglądarki, parsowanie argumentów runnera). W tym przypadku macierz projektów Playwright (`chromium` / `firefox` / `fault`) bez jawnego filtrowania uruchamia Firefox, którego lokalnie nie zainstalowano — fałszywy sygnał jakości przy poprawnej logice biznesowej zweryfikowanej na Chromium.
