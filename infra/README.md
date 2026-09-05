# infra

Runtime infrastructure:

- `compose.yml` — Docker Compose (project name `smarthotel`) with profiles
  `core` (PostgreSQL only), `app` (full stack — services join in Phases 2–8),
  `stubs` (WireMock for external APIs, Phase 7+), `observability` (ELK, Phase 10).
- `postgres/init/` — first-run initialization: `pms`/`pricing` schemas, two
  least-privilege users, `btree_gist` extension (see plan D2, §3.1).
- `elk/` — Filebeat config + exported Kibana saved objects (Phase 10).
- `wiremock/` — stub mappings for Ticketmaster/Gemini used by tests, CI, and offline demo.
- `seed/` — demo-narrative and performance data seeding (Phases 11, 14).

## Usage (from the repository root)

```powershell
Copy-Item .env.example .env    # once; adjust values as needed

docker compose --env-file .env -f infra/compose.yml --profile core up -d --wait
docker compose --env-file .env -f infra/compose.yml --profile core ps
docker compose --env-file .env -f infra/compose.yml --profile core down

# Wipe the database and re-run the init scripts:
docker compose --env-file .env -f infra/compose.yml --profile core down --volumes
```

Taskfile targets (`task up`, `task down`, `task smoke`) will wrap these commands
in Phase 0, step 2.
