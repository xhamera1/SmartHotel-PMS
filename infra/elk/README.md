# Observability (compose profile `observability`)

Single-node Elasticsearch (1g heap) + Kibana + Filebeat Docker autodiscover.
Design notes: [`docs/architecture/observability.md`](../../docs/architecture/observability.md).

## Start

```bash
# from repo root — keep this profile OFF for light day-to-day work
docker compose --env-file .env -f infra/compose.yml \
  --profile app --profile observability up -d --build --wait

bash infra/elk/setup-es.sh          # ILM 7d + dynamic:false template
bash infra/elk/import-kibana.sh     # Data View (@timestamp) + searches + dashboards
```

### Discover error `Cannot read properties of undefined (reading 'isPersisted')`

Przyczyna: brak poprawnego **Data View** z `timeFieldName=@timestamp` (albo stary broken SO). Naprawa:

```bash
# Git Bash / WSL from repo root
bash infra/elk/setup-es.sh
bash infra/elk/import-kibana.sh
```

Albo ręcznie w UI: **Stack Management → Data Views → Create** → index `smarthotel-*` → timestamp `@timestamp` → Set as default.

Potem **Ctrl+Shift+R** na Kibanie → Discover → data view **SmartHotel logs**.

Filebeat 8: flaga to `--strict.perms=false` (nie `-strict…`). Pole biznesowe to `businessEvent` (nie `event` — konflikt z ECS).

- Kibana: http://localhost:5601  
- Elasticsearch: http://localhost:9200  
- Index pattern: `smarthotel-*`

## Smoke

```bash
bash infra/elk/smoke.sh
```

Nightly CI runs the same assertion (`_count > 0` on `smarthotel-*`).

## Trace drill-down (exit criterion)

1. Open saved search **Errors by service** (or any error row).  
2. Copy `traceId`.  
3. Discover KQL: `traceId:"<uuid>"` — should show PMS + pricing lines for that request when apps emit JSON (docker profile).

## Verified example (book + cancel) — 2026-10-31

Status: **OK** (manual guest book + cancel on live compose). Full write-up: [`docs/architecture/observability.md`](../../docs/architecture/observability.md) § *Verified walkthrough*.

Short form — confirmation `X5TW36R6` (`DLX`):

| Time | Signal |
|------|--------|
| 16:27:37 | `businessEvent:ReservationCreated` + `POST /reservations` 201, `traceId:42b99161-…` |
| 16:28:31 | `businessEvent:ReservationCancelled` (`actor:guest`) + `POST …/cancel` 200, `traceId:16a9ff25-…` |

Discover KQL: `confirmationCode:"X5TW36R6"`.

## Files

| File | Role |
|------|------|
| `filebeat.yml` | Autodiscover `smarthotel-*` containers, JSON decode |
| `ilm-policy.json` | Delete after 7 days |
| `index-template.json` | Fixed mapping, `dynamic: false` |
| `kibana-saved-objects.ndjson` | Data view, 4 searches, 2 dashboards |
| `setup-es.sh` / `smoke.sh` / `import-kibana.sh` | Local/CI helpers |
